

from datetime import datetime, timedelta
import schedule
from config import logger, IST
from models import Session, InvestmentSchedule, InvestmentCycle
from utils import get_balance, get_ltp, save_execution_to_db, dhan
from socketio_instance import socketio


def place_cnc_market_buy_order(schedule_id, security_id, withdrawable_balance, ltp, amount, etf_name):
    try:
        if isinstance(security_id, tuple):
            security_id = security_id[0]
        security_id = int(security_id)

        logger.info(f"📦 Attempting to place buy order with SECURITY_ID: {security_id}")

        if ltp <= 0:
            raise ValueError("LTP must be positive to calculate quantity.")
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > withdrawable_balance:
            raise ValueError(f"Amount (₹{amount}) exceeds withdrawable balance (₹{withdrawable_balance}).")

        quantity = int(float(amount) / float(ltp))
        if quantity <= 0:
            raise ValueError("Amount is less than LTP, cannot execute trade.")

        logger.info(f"💵 Withdrawable Balance: ₹{withdrawable_balance}")
        logger.info(f"💰 Amount: ₹{amount}")
        logger.info(f"📊 LTP: ₹{ltp}")
        logger.info(f"🧮 Calculated Quantity: {quantity}")

        response = dhan.place_order(
            tag='',
            transaction_type=dhan.BUY,
            exchange_segment=dhan.NSE,
            product_type=dhan.CNC,
            order_type=dhan.MARKET,
            validity='DAY',
            security_id=str(security_id),
            quantity=quantity,
            disclosed_quantity=0,
            price=0,
            trigger_price=0,
            after_market_order=False,
            amo_time='OPEN',
            bo_profit_value=0,
            bo_stop_loss_Value=0
        )

        session = Session()
        try:
            schedule = session.query(InvestmentSchedule).filter_by(schedule_id=schedule_id).one()
            timestamp = datetime.now(IST)

            if response.get('status') == 'success':
                order_id = response.get('data', {}).get('orderId', 'Unknown')
                logger.info(f"✅ Buy order placed successfully for {quantity} units: Order ID {order_id}")
                socketio.emit('trade_update', {
                    'status': 'success',
                    'order_id': order_id,
                    'quantity': quantity,
                    'security_id': security_id,
                    'amount': amount,
                    'ltp': ltp,
                    'etf_name': etf_name
                })
                schedule.status = 'executed'
                schedule.updated_at = timestamp
                session.commit()
                save_execution_to_db(schedule_id, amount, ltp, quantity, timestamp, 'success')
                return quantity, order_id, None
            else:
                error_message = response.get('remarks', {}).get('error_message', 'Unknown error')
                logger.error(f"❌ Failed to place buy order: {response}")
                socketio.emit('trade_update', {
                    'status': 'error',
                    'message': error_message,
                    'security_id': security_id,
                    'etf_name': etf_name
                })
                schedule.status = 'failed'
                schedule.updated_at = timestamp
                session.commit()
                save_execution_to_db(schedule_id, amount, ltp, quantity, timestamp, 'failed', error_message)
                return None, None, error_message

        except Exception as e:
            logger.error(f"❌ Error updating schedule: {e}", exc_info=True)
            session.rollback()
            return None, None, str(e)
        finally:
            session.close()

    except Exception as e:
        logger.error(f"❌ Exception while placing buy order: {e}", exc_info=True)
        socketio.emit('trade_update', {
            'status': 'error',
            'message': str(e),
            'security_id': security_id,
            'etf_name': etf_name
        })

        session = Session()
        try:
            schedule = session.query(InvestmentSchedule).filter_by(schedule_id=schedule_id).one()
            schedule.status = 'failed'
            schedule.updated_at = datetime.now(IST)
            session.commit()
            save_execution_to_db(schedule_id, amount, ltp, 0, datetime.now(IST), 'failed', str(e))
        except:
            session.rollback()
        finally:
            session.close()

        return None, None, str(e)


def execute_weekly_trade(schedule_id, security_id, amount, etf_name):
    logger.info(f"⏰ Executing scheduled trade: schedule_id={schedule_id}, security_id={security_id}, amount={amount}, etf_name={etf_name} at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}")
    session = Session()
    try:
        schedule = session.query(InvestmentSchedule).filter_by(schedule_id=schedule_id).one()
        if schedule.status not in ["pending", "failed"]:
            logger.info(f"⏭️ Skipping trade for schedule {schedule_id} (status: {schedule.status})")
            return
        cycle = session.query(InvestmentCycle).filter_by(cycle_id=schedule.cycle_id).one()
        if cycle.status != 'active':
            logger.info(f"⏭️ Skipping trade for cycle {cycle.cycle_id} (status: {cycle.status})")
            schedule.status = 'skipped'
            schedule.updated_at = datetime.now(IST)
            session.commit()
            return
        available_balance, withdrawable_balance = get_balance()
        if withdrawable_balance is None:
            logger.error("❌ Failed to fetch balance for weekly trade.")
            schedule.status = 'failed'
            schedule.updated_at = datetime.now(IST)
            session.commit()
            save_execution_to_db(schedule_id, amount, 0, 0, datetime.now(IST), 'failed', 'Failed to fetch balance')
            return
        ltp = get_ltp(security_id)
        if ltp is None:
            logger.error(f"❌ Failed to fetch LTP for security ID {security_id}.")
            schedule.status = 'failed'
            schedule.updated_at = datetime.now(IST)
            session.commit()
            save_execution_to_db(schedule_id, amount, 0, 0, datetime.now(IST), 'failed', 'Failed to fetch LTP')
            return
        quantity = int(float(amount) / float(ltp)) if ltp > 0 else 0
        if quantity <= 0:
            logger.warning("Amount is less than LTP, trade will not execute until amount >= LTP.")
            schedule.status = 'failed'
            schedule.updated_at = datetime.now(IST)
            session.commit()
            save_execution_to_db(schedule_id, amount, ltp, 0, datetime.now(IST), 'failed', 'Amount less than LTP')
            return
        _, order_id, error_message = place_cnc_market_buy_order(schedule_id, security_id, withdrawable_balance, ltp, amount, etf_name)
        if error_message:
            logger.error(f"❌ Weekly trade failed: {error_message}")
        else:
            logger.info(f"✅ Weekly trade executed: Order ID {order_id}, Quantity {quantity}")
            completed_count = session.query(InvestmentSchedule).filter_by(cycle_id=cycle.cycle_id, status='executed').count()
            if completed_count == 5:
                cycle.status = 'completed'
                cycle.updated_at = datetime.now(IST)
                session.commit()
    except Exception as e:
        logger.error(f"❌ Error in execute_weekly_trade: {e}", exc_info=True)
        try:
            schedule = session.query(InvestmentSchedule).filter_by(schedule_id=schedule_id).one()
            schedule.status = 'failed'
            schedule.updated_at = datetime.now(IST)
            session.commit()
            save_execution_to_db(schedule_id, amount, 0, 0, datetime.now(IST), 'failed', str(e))
        except:
            session.rollback()
    finally:
        session.close()

def schedule_weekly_trades(cycle_id, security_id, total_amount, start_datetime, etf_name):
    session = Session()
    try:
        scheduled_times = []
        weekly_amount = total_amount / 5
        schedule_entries = []

        for week in range(5):
            execution_datetime = start_datetime + timedelta(weeks=week)
            schedule_entry = InvestmentSchedule(
                cycle_id=cycle_id,
                week_number=week + 1,
                execution_date=execution_datetime.date(),
                execution_time=execution_datetime.time(),
                amount=weekly_amount,
                status='pending'
            )
            session.add(schedule_entry)
            schedule_entries.append(schedule_entry)
            scheduled_times.append(execution_datetime.isoformat())

        session.flush()
        session.commit()
        logger.info(f"✅ Saved {len(schedule_entries)} schedules for cycle {cycle_id} to database")

        for week, schedule_entry in enumerate(schedule_entries):
            execution_datetime = start_datetime + timedelta(weeks=week)
            time_str = execution_datetime.strftime("%H:%M")
            target_date = execution_datetime.date()

            def trade_job(schedule_id=schedule_entry.schedule_id, security_id=security_id, amount=weekly_amount, etf_name=etf_name, target_date=target_date):
                now = datetime.now(IST)
                if now.date() != target_date:
                    logger.debug(f"⏭️ Skipping job for schedule_id={schedule_id}, not today ({now.date()} != {target_date})")
                    return
                execute_weekly_trade(schedule_id, security_id, amount, etf_name)

            schedule.every().day.at(time_str).do(trade_job).tag(f"trade_{cycle_id}_{week}")
            logger.info(f"📅 Job scheduled for {target_date} at {time_str} [Week {week + 1}]")

        logger.info("🗓️ Current Scheduled Jobs:")
        for job in schedule.jobs:
            logger.info(f"⏰ {job}")

        return scheduled_times, total_amount

    except Exception as e:
        logger.error(f"❌ Error scheduling trades: {e}", exc_info=True)
        session.rollback()
        return None, None
    finally:
        session.close()

def unschedule_jobs_for_cycle(cycle_id):
    tags_to_remove = [f"trade_{cycle_id}_{i}" for i in range(5)]
    count = 0
    for tag in tags_to_remove:
        schedule.clear(tag)
        count += 1
    logger.info(f"🛑 Unscheduled {count} jobs for cycle {cycle_id}")