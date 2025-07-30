
import React, { useState } from 'react';
import { X, Plus, TrendingUp, CalendarIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

interface AddCycleFormProps {
  onSubmit: (name: string, amount: number, startDate: Date) => void;
  onCancel: () => void;
}

export const AddCycleForm: React.FC<AddCycleFormProps> = ({ onSubmit, onCancel }) => {
  const [name, setName] = useState('');
  const [amount, setAmount] = useState<number>(0);
  const [startDate, setStartDate] = useState<Date>(new Date());

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim() && amount > 0 && startDate) {
      onSubmit(name.trim(), amount, startDate);
    }
  };

  const weeklyAmount = amount / 5;

  return (
    <div className="bg-white rounded-2xl border-2 border-primary/20 p-8 shadow-2xl max-w-md w-full mx-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
         
          <div>
            <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">Add New Cycle</h2>
            <p className="text-muted-foreground text-sm">Create a new trading strategy</p>
          </div>
        </div>
        <button
          onClick={onCancel}
          className="p-2 rounded-lg hover:bg-muted/50 transition-colors border border-border/50"
        >
          <X className="w-5 h-5 text-muted-foreground" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Strategy Name */}
        <div className="space-y-2">
          <Label htmlFor="name" className="text-foreground font-medium">
            ETF Name
          </Label>
          <Input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., ABC"
            className="bg-background border-primary/30 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary/20"
            required
          />
        </div>

        {/* Total Amount */}
        <div className="space-y-2">
          <Label htmlFor="amount" className="text-foreground font-medium">
            Total Amount (₹)
          </Label>
          <Input
            id="amount"
            type="number"
            value={amount || ''}
            onChange={(e) => setAmount(Number(e.target.value))}
            placeholder="e.g., 1000000"
            className="bg-background border-primary/30 text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary/20"
            required
            min="1"
          />
        </div>

        {/* Start Date */}
        <div className="space-y-2">
          <Label className="text-foreground font-medium">
            Start Date
          </Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  "w-full justify-start text-left font-normal bg-background border-primary/30 hover:bg-primary/5",
                  !startDate && "text-muted-foreground"
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {startDate ? format(startDate, "PPP") : <span>Pick a date</span>}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={startDate}
                onSelect={(date) => date && setStartDate(date)}
                initialFocus
                className="pointer-events-auto"
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Weekly Breakdown Preview */}
        {amount > 0 && (
          <div className="bg-gradient-to-r from-primary/5 to-purple/5 rounded-lg p-4 border border-primary/20">
            <div className="flex items-center space-x-2 mb-3">
              <TrendingUp className="w-4 h-4 text-primary" />
              <span className="text-primary font-medium text-sm">Weekly Breakdown</span>
            </div>
            <div className="grid grid-cols-5 gap-2">
              {Array.from({ length: 5 }, (_, index) => (
                <div key={index} className="bg-gradient-to-br from-background to-primary/5 rounded-lg p-2 text-center border border-primary/20">
                  <div className="text-xs text-muted-foreground mb-1">Week {index + 1}</div>
                  <div className="text-sm text-foreground font-semibold">
                    ₹{weeklyAmount.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3 pt-4">
          <Button
            type="button"
            onClick={onCancel}
            variant="outline"
            className="flex-1 border-border text-foreground hover:bg-muted/50"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={!name.trim() || amount <= 0 || !startDate}
            className="flex-1 bg-gradient-to-r from-primary to-purple hover:from-primary/90 hover:to-purple/90 text-white font-semibold shadow-lg disabled:opacity-50 border-0"
          >
            Create Cycle
          </Button>
        </div>
      </form>
    </div>
  );
};
