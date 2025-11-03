import { toast } from "@/components/ui/sonner";

interface ApiError {
  message: string;
  status: "error";
}

export const showApiError = (error: ApiError | string) => {
  const message = typeof error === "string" ? error : error.message;
  console.log("Showing error toast:", message); // Debug log
  
  // Use the toast from our UI components
  toast.error(message);
  
  // Fallback: also try direct sonner import
  try {
    const { toast: sonnerToast } = require("sonner");
    sonnerToast.error(message);
  } catch (e) {
    console.log("Fallback toast failed:", e);
  }
};
