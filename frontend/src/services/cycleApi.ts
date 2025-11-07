import { showApiError } from '@/lib/toast-utils';

 const BASE_URL = 'https://etf-backend.codecatalystworks.com/api';
//  const BASE_URL = ' http://127.0.0.1:5000/api';
export interface CycleApiResponse {
  success: boolean;
  message?: string;
  data?: any;
}

interface ApiErrorResponse {
  message: string;
  status: "error";
}

const handleApiError = async (response: Response): Promise<string> => {
  console.log("Handling API error, status:", response.status); // Debug log
  try {
    const errorData: ApiErrorResponse = await response.json();
    console.log("Error data:", errorData); // Debug log
    const errorMessage = errorData.message || `HTTP error! status: ${response.status}`;
    showApiError(errorMessage);
    return errorMessage;
  } catch (parseError) {
    console.log("Failed to parse error response:", parseError); // Debug log
    const errorMessage = `HTTP error! status: ${response.status}`;
    showApiError(errorMessage);
    return errorMessage;
  }
};

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
        const errorMessage = await handleApiError(response);
        return { success: false, message: errorMessage };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to pause cycle';
      showApiError(errorMessage);
      return { success: false, message: errorMessage };
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
        const errorMessage = await handleApiError(response);
        return { success: false, message: errorMessage };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to resume cycle';
      showApiError(errorMessage);
      return { success: false, message: errorMessage };
    }
  }

  /**
   * Get all ETF details
   */
  static async getAllEtfDetails(): Promise<CycleApiResponse> {
    try {
      const response = await fetch(`${BASE_URL}/all_etf_details`);
      
      if (!response.ok) {
        const errorMessage = await handleApiError(response);
        return { success: false, message: errorMessage };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch ETF details';
      showApiError(errorMessage);
      return { success: false, message: errorMessage };
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
        const errorMessage = await handleApiError(response);
        return { success: false, message: errorMessage };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to schedule ETF';
      showApiError(errorMessage);
      return { success: false, message: errorMessage };
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
        const errorMessage = await handleApiError(response);
        return { success: false, message: errorMessage };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update schedule';
      showApiError(errorMessage);
      return { success: false, message: errorMessage };
    }
  }
}
