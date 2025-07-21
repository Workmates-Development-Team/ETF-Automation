from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask.json.provider import DefaultJSONProvider
import numpy as np
import threading
import time
from datetime import datetime
import schedule
from sqlalchemy import func
from config import logger, IST
from models import Session, ETF, InvestmentCycle, InvestmentSchedule
from utils import get_security_details, get_ltp, dhan, get_balance
from socketio_instance import socketio
from trade import place_cnc_market_buy_order, execute_weekly_trade, schedule_weekly_trades, unschedule_jobs_for_cycle

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/socket.io/*": {"origins": "*"}})
socketio.init_app(app)

# Custom JSON Provider to handle NumPy types
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

app.json = CustomJSONProvider(app)

def run_scheduler():
    while True:
        logger.debug(f"🔄 Running scheduler loop at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}")
        schedule.run_pending()
        time.sleep(1)

def reload_pending_schedules():
    """
    Reloads all pending schedules from the database and registers them with the scheduler.
    Marks past schedules as 'expired'.
    """
    session = Session()
    try:
        logger.info("🔄 Reloading pending schedules from database on server startup")
        now = datetime.now(IST)
        
        pending_schedules = (
            session.query(InvestmentSchedule)
            .join(InvestmentCycle, InvestmentSchedule.cycle_id == InvestmentCycle.cycle_id)
            .filter(
                InvestmentSchedule.status == "pending",
                InvestmentCycle.status == "active"
            )
            .all()
        )

        if not pending_schedules:
            logger.info("ℹ️ No pending schedules found in database")
            return

        for schedule_item in pending_schedules:
            cycle = session.query(InvestmentCycle).filter_by(cycle_id=schedule_item.cycle_id).first()
            etf = session.query(ETF).filter_by(etf_id=cycle.etf_id).first()
            security_id = get_security_details(etf.etf_name)

            if not security_id:
                logger.error(f"⚠️ Could not fetch security details for ETF '{etf.etf_name}' for schedule_id={schedule_item.schedule_id}")
                continue

            execution_datetime = datetime.combine(
                schedule_item.execution_date,
                schedule_item.execution_time
            ).replace(tzinfo=IST)

            if execution_datetime <= now:
                schedule_item.status = "expired"
                session.commit()
                logger.info(f"⏭️ Marked schedule_id={schedule_item.schedule_id} as expired (execution_datetime={execution_datetime})")
                continue

            time_str = execution_datetime.strftime("%H:%M")
            target_date = schedule_item.execution_date

            def scheduled_trade(
                schedule_id=schedule_item.schedule_id,
                security_id=security_id,
                amount=schedule_item.amount,
                etf_name=etf.etf_name,
                target_date=target_date
            ):
                now = datetime.now(IST)
                if now.date() != target_date:
                    return
                logger.info(f"🚀 Executing scheduled trade for schedule_id={schedule_id}")
                execute_weekly_trade(schedule_id, security_id, amount, etf_name)

            job_tag = f"trade_{schedule_item.cycle_id}_{schedule_item.week_number - 1}"
            schedule.every().day.at(time_str).do(scheduled_trade).tag(job_tag)
            logger.info(
                f"✅ Scheduled job for schedule_id={schedule_item.schedule_id}, "
                f"cycle_id={schedule_item.cycle_id}, week={schedule_item.week_number}, "
                f"at {time_str} on {target_date}"
            )

        logger.info(f"✅ Successfully reloaded {len(pending_schedules)} pending schedules")
        
    except Exception as e:
        logger.error(f"❌ Error reloading pending schedules: {e}", exc_info=True)
    finally:
        session.close()

@app.errorhandler(400)
def bad_request_error(error):
    logger.error(f"400 Bad Request: {error}")
    return jsonify({
        "status": "error",
        "message": str(error.description) if hasattr(error, 'description') else "Bad Request"
    }), 400

@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"500 Internal Server Error: {error}")
    return jsonify({
        "status": "error",
        "message": str(error.description) if hasattr(error, 'description') else "Internal Server Error"
    }), 500

@app.route("/api/pause_cycle", methods=["POST"])
def pause_cycle():
    session = Session()
    try:
        data = request.get_json()
        cycle_id = data.get("cycle_id")
        if not cycle_id:
            return jsonify({"status": "error", "message": "Missing cycle_id"}), 400

        cycle = session.query(InvestmentCycle).filter_by(cycle_id=cycle_id).first()
        if not cycle:
            return jsonify({"status": "error", "message": "Cycle not found"}), 404

        if cycle.status == "paused":
            return jsonify({"status": "error", "message": "Cycle already paused"}), 400

        cycle.status = "paused"
        session.commit()
        unschedule_jobs_for_cycle(cycle_id)

        logger.info(f"⏸️ Paused cycle {cycle_id}")
        return jsonify({"status": "success", "message": f"Cycle {cycle_id} paused"})

    except Exception as e:
        logger.error(f"❌ Error in /api/pause_cycle: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/resume_cycle", methods=["POST"])
def resume_cycle():
    session = Session()
    try:
        data = request.get_json()
        cycle_id = data.get("cycle_id")
        if not cycle_id:
            return jsonify({"status": "error", "message": "Missing cycle_id"}), 400

        cycle = session.query(InvestmentCycle).filter_by(cycle_id=cycle_id).first()
        if not cycle:
            return jsonify({"status": "error", "message": "Cycle not found"}), 404

        if cycle.status != "paused":
            return jsonify({"status": "error", "message": "Cycle is not paused"}), 400

        etf = session.query(ETF).filter_by(etf_id=cycle.etf_id).first()
        schedules = session.query(InvestmentSchedule).filter_by(cycle_id=cycle_id, status="pending").all()
        security_id = get_security_details(etf.etf_name)
        now = datetime.now(IST)

        for s in schedules:
            dt = datetime.combine(s.execution_date, s.execution_time).replace(tzinfo=IST)
            if dt > now:
                time_str = dt.strftime("%H:%M")
                target_date = s.execution_date

                def resume_trade(schedule_id=s.schedule_id, security_id=security_id, amount=s.amount, etf_name=etf.etf_name, target_date=target_date):
                    now = datetime.now(IST)
                    if now.date() != target_date:
                        return
                    execute_weekly_trade(schedule_id, security_id, amount, etf_name)

                schedule.every().day.at(time_str).do(resume_trade).tag(f"trade_{cycle_id}_{s.week_number - 1}")
                logger.info(f"🔁 Rescheduled Week {s.week_number} for cycle {cycle_id} at {time_str} on {target_date}")

        cycle.status = "active"
        session.commit()
        return jsonify({"status": "success", "message": f"Cycle {cycle_id} resumed with {len(schedules)} jobs"})

    except Exception as e:
        logger.error(f"❌ Error in /api/resume_cycle: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/update_schedule", methods=["POST"])
def update_schedule():
    session = Session()
    try:
        data = request.get_json()
        schedule_id = data.get("schedule_id")
        new_amount = data.get("amount")
        new_date = data.get("execution_date")
        new_time = data.get("execution_time")

        if not schedule_id:
            return jsonify({"status": "error", "message": "Missing schedule_id"}), 400

        schedule_item = session.query(InvestmentSchedule).filter_by(schedule_id=schedule_id).first()
        if not schedule_item:
            return jsonify({"status": "error", "message": "Schedule not found"}), 404

        changes = []
        if new_amount is not None:
            try:
                new_amount = float(new_amount)
                if new_amount <= 0:
                    return jsonify({"status": "error", "message": "Amount must be positive"}), 400
                schedule_item.amount = new_amount
                changes.append("amount")
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid amount format"}), 400

        if new_date:
            try:
                parsed_date = datetime.strptime(new_date, "%Y-%m-%d").date()
                schedule_item.execution_date = parsed_date
                changes.append("execution_date")
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid date format, must be YYYY-MM-DD"}), 400

        if new_time:
            try:
                parsed_time = datetime.strptime(new_time, "%H:%M:%S").time()
                schedule_item.execution_time = parsed_time
                changes.append("execution_time")
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid time format, must be HH:MM:SS"}), 400

        if not changes:
            return jsonify({"status": "error", "message": "No valid update fields provided"}), 400

        schedule_item.updated_at = datetime.now(IST)

        cycle = session.query(InvestmentCycle).filter_by(cycle_id=schedule_item.cycle_id).first()
        total = session.query(InvestmentSchedule).filter_by(cycle_id=cycle.cycle_id).with_entities(
            func.sum(InvestmentSchedule.amount)
        ).scalar() or 0.0

        cycle.total_amount = total
        cycle.updated_at = datetime.now(IST)

        session.commit()

        try:
            schedule.clear(f"trade_{cycle.cycle_id}_{schedule_item.week_number - 1}")
            logger.info(f"🗑️ Cleared old job for schedule_id={schedule_item.schedule_id}")

            now = datetime.now(IST)
            updated_dt = datetime.combine(schedule_item.execution_date, schedule_item.execution_time).replace(tzinfo=IST)

            if schedule_item.status in ["pending", "failed"] and updated_dt > now:
                time_str = updated_dt.strftime("%H:%M")
                target_date = schedule_item.execution_date
                etf = session.query(ETF).filter_by(etf_id=cycle.etf_id).first()
                security_id = get_security_details(etf.etf_name)

                def updated_trade(schedule_id=schedule_item.schedule_id, security_id=security_id, amount=schedule_item.amount, etf_name=etf.etf_name, target_date=target_date):
                    now = datetime.now(IST)
                    if now.date() != target_date:
                        return
                    execute_weekly_trade(schedule_id, security_id, amount, etf_name)

                schedule.every().day.at(time_str).do(updated_trade).tag(f"trade_{cycle.cycle_id}_{schedule_item.week_number - 1}")
                logger.info(f"🆕 Rescheduled job for schedule_id={schedule_item.schedule_id} at {time_str} on {target_date}")

        except Exception as e:
            logger.warning(f"⚠️ Error during rescheduling: {e}")

        return jsonify({
            "status": "success",
            "message": f"Updated schedule {schedule_id}",
            "updated_fields": changes,
            "new_total_amount": total
        })

    except Exception as e:
        logger.error(f"❌ Error in /api/update_schedule: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/etf_details/<etf_name>", methods=["GET"])
def get_etf_details(etf_name):
    session = Session()
    try:
        etf = session.query(ETF).filter_by(etf_name=etf_name.strip()).first()
        if not etf:
            logger.error(f"ETF '{etf_name}' not found in database")
            return jsonify({"status": "error", "message": f"ETF '{etf_name}' not found"}), 404

        cycles = session.query(InvestmentCycle).filter_by(etf_id=etf.etf_id).all()
        cycle_list = []
        total_invested = 0.0

        for cycle in cycles:
            schedules = session.query(InvestmentSchedule).filter_by(cycle_id=cycle.cycle_id).order_by(InvestmentSchedule.week_number).all()
            schedule_list = []
            for s in schedules:
                schedule_list.append({
                    "schedule_id": s.schedule_id,
                    "week_number": s.week_number,
                    "execution_date": s.execution_date.isoformat(),
                    "execution_time": s.execution_time.strftime("%H:%M:%S"),
                    "amount": float(s.amount),
                    "quantity": int(s.quantity),  # Include quantity
                    "status": s.status,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat()
                })
                if s.status == "executed":
                    total_invested += float(s.amount)

            cycle_list.append({
                "cycle_id": cycle.cycle_id,
                "total_amount": float(cycle.total_amount),
                "start_date": cycle.start_date.isoformat(),
                "status": cycle.status,
                "created_at": cycle.created_at.isoformat(),
                "updated_at": cycle.updated_at.isoformat(),
                "schedules": schedule_list
            })

        holdings = []
        try:
            response = dhan.get_holdings()
            if response and response.get("status") == "success" and "data" in response:
                holdings = response["data"]
                logger.info(f"Fetched {len(holdings)} holdings from Dhan")
            else:
                logger.error(f"Failed to fetch holdings. Response: {response}")
                return jsonify({
                    "status": "error",
                    "message": f"Failed to fetch holdings: {response.get('remarks', 'Unknown error')}"
                }), 500
        except Exception as e:
            logger.error(f"Exception while fetching holdings: {e}", exc_info=True)
            return jsonify({
                "status": "error",
                "message": f"Failed to fetch holdings: {str(e)}"
            }), 500

        holding_qty = 0
        current_value = 0.0
        avg_cost_price = 0.0
        security_id, symbol_name = get_security_details(etf.etf_name)
        
        if not security_id:
            logger.error(f"Could not fetch security details for ETF '{etf_name}'")
            return jsonify({
                "status": "error",
                "message": f"Could not fetch security details for ETF '{etf_name}'"
            }), 500

        ltp = None
        holding_details = None
        if holdings:
            for holding in holdings:
                if int(holding.get("securityId")) == int(security_id):
                    holding_qty = int(holding.get("availableQty", 0))
                    ltp = float(holding.get("lastTradedPrice", 0.0))
                    avg_cost_price = float(holding.get("avgCostPrice", 0.0))
                    holding_details = holding
                    current_value = holding_qty * ltp
                    break

        if ltp is None or ltp == 0.0:
            ltp = get_ltp(security_id)
            if ltp is None:
                logger.error(f"Could not fetch LTP for ETF '{etf_name}' (security_id: {security_id})")
                ltp = 0.0
            current_value = holding_qty * ltp

        profit_percent = ((current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0.0

        response = {
            "status": "success",
            "etf": {
                "etf_id": etf.etf_id,
                "etf_name": etf.etf_name,
                "full_name": symbol_name,
                "description": etf.description,
                "created_at": etf.created_at.isoformat(),
                "investment_cycles": cycle_list,
                "total_invested": round(float(total_invested), 2),
                "current_value": round(float(current_value), 2),
                "profit_percent": round(float(profit_percent), 2),
                "holding_quantity": holding_qty,
                "avg_cost_price": round(float(avg_cost_price), 2),
                "ltp": round(float(ltp), 2) if ltp else None,
                "holding_details": holding_details
            }
        }

        logger.info(f"Successfully fetched details for ETF '{etf_name}': "
                    f"Total Invested: ₹{total_invested:.2f}, "
                    f"Current Value: ₹{current_value:.2f}, "
                    f"Profit: {profit_percent:.2f}%, "
                    f"Holding Quantity: {holding_qty}, "
                    f"Avg Cost Price: ₹{avg_cost_price:.2f}, "
                    f"LTP: ₹{ltp:.2f}")
        
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in /api/etf_details/{etf_name}: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}), 500
    finally:
        session.close()

@app.route("/api/schedule_etf", methods=["POST"])
def api_schedule_etf():
    session = Session()
    try:
        data = request.get_json()
        if not data or "etf_name" not in data or "total_amount" not in data or "start_date" not in data:
            logger.error("Missing etf_name, total_amount, or start_date in request body")
            return jsonify({"status": "error", "message": "Missing etf_name, total_amount, or start_date in request body"}), 400
        etf_name = data["etf_name"].strip()
        total_amount = float(data["total_amount"])
        start_date = data["start_date"]
        start_time = data.get("start_time", "15:00:00")

        if total_amount <= 0:
            logger.error("Total amount must be positive.")
            return jsonify({"status": "error", "message": "Total amount must be positive."}), 400

        try:
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
        except ValueError as e:
            logger.error(f"Invalid date or time format: {e}")
            return jsonify({"status": "error", "message": f"Invalid date or time format. Use 'YYYY-MM-DD' for start_date and 'HH:MM:SS' for start_time. Error: {str(e)}"}), 400

        etf = session.query(ETF).filter_by(etf_name=etf_name).first()
        if not etf:
            etf = ETF(etf_name=etf_name, description=f"ETF {etf_name}")
            session.add(etf)
            session.flush()
            logger.info(f"✅ Created new ETF: {etf_name}")
        etf_id = etf.etf_id

        security_id = get_security_details(etf_name)
        if not security_id:
            logger.error(f"Could not fetch security details for ETF '{etf_name}'.")
            return jsonify({"status": "error", "message": f"Could not fetch security details for ETF '{etf_name}'."}), 500

        available_balance, withdrawable_balance = get_balance()
        if withdrawable_balance is None:
            logger.error("Could not fetch withdrawable balance.")
            return jsonify({"status": "error", "message": "Could not fetch withdrawable balance."}), 500
        if total_amount > withdrawable_balance:
            logger.error(f"Total amount (₹{total_amount}) exceeds withdrawable balance (₹{withdrawable_balance}).")
            return jsonify({
                "status": "error",
                "message": f"Total amount (₹{total_amount}) exceeds withdrawable balance (₹{withdrawable_balance})."
            }), 400

        cycle = InvestmentCycle(
            etf_id=etf_id,
            total_amount=total_amount,
            start_date=start_datetime.date(),
            status='active'
        )
        session.add(cycle)
        session.flush()
        cycle_id = cycle.cycle_id

        scheduled_times, total_amount = schedule_weekly_trades(cycle_id, security_id, total_amount, start_datetime, etf_name)
        if not scheduled_times:
            logger.error("Failed to schedule trades.")
            return jsonify({"status": "error", "message": "Failed to schedule trades."}), 500

        session.commit()

        logger.info("=== ETF Schedule Details ===")
        logger.info(f"ETF Name: {etf_name}")
        logger.info(f"Total Amount: ₹{total_amount:.2f}")
        logger.info(f"Weekly Amount: ₹{total_amount / 5:.2f}")
        logger.info(f"Cycle ID: {cycle_id}")
        logger.info("Schedule:")
        for i, dt in enumerate(scheduled_times, 1):
            logger.info(f"  Week {i}: {datetime.fromisoformat(dt).strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("==========================")

        return jsonify({
            "status": "success",
            "etf_name": etf_name,
            "total_amount": total_amount,
            "weekly_amount": total_amount / 5,
            "schedule": [
                f"{datetime.fromisoformat(dt).strftime('%Y-%m-%d %H:%M:%S')}" for dt in scheduled_times
            ],
            "cycle_id": cycle_id
        })

    except ValueError as e:
        logger.error(f"🚨 Validation Error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"❌ Error in /api/schedule_etf: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}), 500
    finally:
        session.close()

@app.route("/api/all_etf_details", methods=["GET"])
def get_all_etf_details():
    session = Session()
    try:
        etfs = session.query(ETF).all()

        response = dhan.get_holdings()
        logger.info(f"[Dhan Holdings API Response] => {response}")

        holdings = response.get("data", []) if response and response.get("status") == "success" else []

        strategies = []

        for etf in etfs:
            security_id, symbol_name = get_security_details(etf.etf_name)
            if not security_id:
                logger.warning(f"Could not fetch security details for {etf.etf_name}")
                symbol_name = etf.etf_name

            cycles = session.query(InvestmentCycle).filter_by(etf_id=etf.etf_id).all()
            holding_qty = 0
            ltp = 0.0
            avg_cost_price = 0.0
            current_value = 0.0
            weeks = []

            holding_details = next((h for h in holdings if int(h.get("securityId")) == int(security_id)), None)
            if holding_details:
                holding_qty = int(holding_details.get("availableQty", 0))
                ltp = float(holding_details.get("lastTradedPrice", 0.0))
                avg_cost_price = float(holding_details.get("avgCostPrice", 0.0))
                current_value = holding_qty * ltp
            else:
                ltp = get_ltp(security_id) or 0.0
                current_value = holding_qty * ltp

            total_invested = avg_cost_price * holding_qty

            total_cycle_count = 0
            for cycle in cycles:
                total_cycle_count += 1
                schedules = (
                    session.query(InvestmentSchedule)
                    .filter_by(cycle_id=cycle.cycle_id)
                    .order_by(InvestmentSchedule.week_number)
                    .all()
                )
                for s in schedules:
                    weeks.append({
                        "id": f"{etf.etf_id}-{s.week_number}",
                        "weekNumber": s.week_number,
                        "amount": float(s.amount),
                        "date": s.execution_date.strftime("%d/%m/%Y"),
                        "ltp": round(ltp, 2),
                        "qty": int(s.quantity),  # Use stored quantity
                        "status": s.status
                    })

            profit_percent = ((current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0.0

            strategy = {
                "id": str(etf.etf_id),
                "name": etf.etf_name,
                "full_name": symbol_name,
                "totalAmount": round(total_invested, 2),
                "totalQty": holding_qty,
                "avgCostPrice": round(avg_cost_price, 2),
                "ltp": round(ltp, 2),
                "currentValue": round(current_value, 2),
                "profit": round(profit_percent, 2),
                "status": cycles[0].status if cycles else "unknown",
                "totalCount": total_cycle_count,
                "startDate": cycles[0].start_date.strftime("%d/%m/%Y") if cycles else None,
                "weeks": weeks
            }

            strategies.append(strategy)

        return jsonify(strategies)

    except Exception as e:
        logger.error(f"Error in /api/all_etf_details: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}), 500
    finally:
        session.close()

if __name__ == "__main__":
    reload_pending_schedules()
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    socketio.run(app, debug=True)