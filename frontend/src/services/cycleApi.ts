const BASE_URL = 'https://etf-backend.codecatalystworks.com/api';

export interface CycleApiResponse {
  success: boolean;
  message?: string;
  data?: any;
}

export class CycleApiService {
  /**
   * Pause a cycle
   * @param cycleId - The ID of the cycle to pause
   */
  static async pauseCycle(cycleId: number): Promise<CycleApiResponse> {
    try {
      const response = await fetch(`${BASE_URL}/pause_cycle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cycle_id: cycleId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('Error pausing cycle:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to pause cycle',
      };
    }
  }

  /**
   * Resume a cycle
   * @param cycleId - The ID of the cycle to resume
   */
  static async resumeCycle(cycleId: number): Promise<CycleApiResponse> {
    try {
      const response = await fetch(`${BASE_URL}/resume_cycle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cycle_id: cycleId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('Error resuming cycle:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to resume cycle',
      };
    }
  }

  /**
   * Get all ETF details
   */
  static async getAllEtfDetails(): Promise<CycleApiResponse> {
    try {
      const response = await fetch(`${BASE_URL}/all_etf_details`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('Error fetching ETF details:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to fetch ETF details',
      };
    }
  }

  /**
   * Schedule a new ETF
   */
  static async scheduleEtf(totalAmount: number, etfName: string, startDate: string): Promise<CycleApiResponse> {
    try {
      const response = await fetch(`${BASE_URL}/schedule_etf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          total_amount: totalAmount,
          etf_name: etfName,
          start_date: startDate,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('Error scheduling ETF:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to schedule ETF',
      };
    }
  }

  /**
   * Update a schedule
   */
  static async updateSchedule(scheduleId: string, amount: number, executionDate: string, executionTime: string = "15:36:00"): Promise<CycleApiResponse> {
    try {
      const response = await fetch(`${BASE_URL}/update_schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          schedule_id: scheduleId,
          amount,
          execution_date: executionDate,
          execution_time: executionTime,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('Error updating schedule:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to update schedule',
      };
    }
  }
}
