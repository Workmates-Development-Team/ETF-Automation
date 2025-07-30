import React, { useState } from 'react';
import { Calendar, DollarSign, Edit3, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Week {
  id: string;
  weekNumber: number;
  amount: number;
  date: string;
  ltp: number;
  qty: number;
  status: 'executed' | 'active' | 'inactive' | 'pending' | 'failed';
}

interface WeekCardProps {
  week: Week;
  onUpdate: (updates: Partial<Week>) => void;
  isDisabled: boolean;
}

export const WeekCard: React.FC<WeekCardProps> = ({ week, onUpdate, isDisabled }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValues, setEditValues] = useState({
    amount: week.amount,
    date: week.date
  });

  const getStatusStyles = () => {
    switch (week.status) {
      case 'executed':
        return 'bg-gradient-to-br from-success/20 to-teal/20 border-success/50 text-success-foreground shadow-lg shadow-success/10';
      case 'active':
        return 'bg-gradient-to-br from-primary/20 to-purple/20 border-primary/50 text-primary-foreground shadow-lg shadow-primary/20';
      case 'pending':
        return 'bg-gradient-to-br from-muted/40 to-muted/60 border-muted text-muted-foreground';
      default:
        return 'bg-muted/50 border-muted text-muted-foreground';
    }
  };

  const getWeekNumberColor = () => {
    switch (week.status) {
      case 'executed':
        return 'bg-gradient-to-r from-success to-teal';
      case 'active':
        return 'bg-gradient-to-r from-primary to-purple';
      case 'pending':
        return 'bg-gradient-to-r from-muted-foreground to-muted-foreground';
      case 'failed':
        return 'bg-gradient-to-r from-red-600 to-red-600';
      default:
        return 'bg-gradient-to-r from-muted to-muted';
    }
  };

  const handleSave = () => {
    onUpdate({
      amount: editValues.amount,
      date: editValues.date
    });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValues({
      amount: week.amount,
      date: week.date
    });
    setIsEditing(false);
  };

  const executeWeek = () => {
    onUpdate({ status: 'executed' });
  };

  return (
    <div className={`
      relative rounded-xl border-2 p-4 backdrop-blur-sm transition-all duration-300 hover:scale-105 
      ${getStatusStyles()}
      ${isDisabled ? 'opacity-50' : ''}
    `}>
      {/* Week Number Badge */}
      <div className={`absolute -top-2 -left-2 w-8 h-8 ${getWeekNumberColor()} rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg`}>
        {week.weekNumber}
      </div>

      {/* Edit Button */}
      {!isEditing && week.status !== 'executed' && !isDisabled && (
        <button
          onClick={() => setIsEditing(true)}
          className="absolute top-2 right-2 p-1 rounded-md bg-card/50 hover:bg-card/70 transition-colors border border-border/50"
        >
          <Edit3 className="w-3 h-3 text-foreground" />
        </button>
      )}

      <div className="mt-2 space-y-3">
        {isEditing ? (
          // Edit Mode
          <div className="space-y-3">
            <div>
              <Label className="text-xs text-foreground">Amount</Label>
              <Input
                type="number"
                value={editValues.amount}
                onChange={(e) => setEditValues(prev => ({ ...prev, amount: Number(e.target.value) }))}
                className="h-8 text-xs bg-background border-border text-foreground"
              />
            </div>
            <div>
              <Label className="text-xs text-foreground">Date</Label>
              <Input
                type="text"
                value={editValues.date}
                onChange={(e) => setEditValues(prev => ({ ...prev, date: e.target.value }))}
                className="h-8 text-xs bg-background border-border text-foreground"
                placeholder="DD/MM/YYYY"
              />
            </div>
            <div className="flex space-x-2">
              <Button
                onClick={handleSave}
                size="sm"
                className="h-6 px-2 bg-gradient-to-r from-success to-teal hover:from-success/90 hover:to-teal/90 text-xs text-white border-0"
              >
                <Check className="w-3 h-3" />
              </Button>
              <Button
                onClick={handleCancel}
                size="sm"
                variant="outline"
                className="h-6 px-2 text-xs border-border"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          </div>
        ) : (
          // View Mode
          <>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1">
                <DollarSign className="w-3 h-3" />
                <span className="text-sm font-semibold">₹{week.amount.toLocaleString()}</span>
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex items-center space-x-1 text-muted-foreground">
                <Calendar className="w-3 h-3" />
                <span>{week.date}</span>
              </div>
              <div className="text-muted-foreground">LTP: ₹{week.ltp}</div>
              <div className="text-muted-foreground">Qty: {week.qty}</div>
            </div>

            {/* Status & Action */}
            <div className="pt-2">
              {week.status === 'executed' && (
                <div className="text-success text-xs font-semibold flex items-center">
                  <Check className="w-3 h-3 mr-1" />
                  Executed
                </div>
              )}
              {week.status === 'active' && !isDisabled && (
                <Button
                  onClick={executeWeek}
                  size="sm"
                  className="w-full h-6 text-xs bg-gradient-to-r from-primary to-purple hover:from-primary/90 hover:to-purple/90 text-white font-semibold shadow-lg border-0"
                >
                  Execute
                </Button>
              )}
              {week.status === 'inactive' && (
                <div className="text-muted-foreground text-xs font-semibold text-center">
                  Inactive
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
