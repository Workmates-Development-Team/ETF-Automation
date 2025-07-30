
import React from 'react';
import { Play, Pause, TrendingUp, Hash, DollarSign, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { WeekCard } from '@/components/WeekCard';

interface Week {
  id: string;
  weekNumber: number;
  amount: number;
  date: string;
  ltp: number;
  qty: number;
  status: 'executed' | 'active' | 'inactive';
}

interface Cycle {
  id: string;
  name: string;
  totalAmount: number;
  totalQty: number;
  profit: number;
  status: 'active' | 'paused' | 'completed';
  weeks: Week[];
  totalCount: number;
  startDate?: string;
}

interface CycleCardProps {
  cycle: Cycle;
  onUpdate: (cycle: Cycle) => void;
  onToggleStatus: (cycleId: string) => void;
  isLoading?: boolean;
}

export const CycleCard: React.FC<CycleCardProps> = ({ 
  cycle, 
  onUpdate, 
  onToggleStatus,
  isLoading = false
}) => {
  const updateWeek = (weekId: string, updates: Partial<Week>) => {
    const updatedWeeks = cycle.weeks.map(week =>
      week.id === weekId ? { ...week, ...updates } : week
    );

    console.log(cycle)
    
    onUpdate({ id: weekId,  updates});
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-success border-success/30';
      case 'paused': return 'bg-warning border-warning/30';
      case 'completed': return 'bg-info border-info/30';
      default: return 'bg-muted border-muted/30';
    }
  };

  const getStatusGradient = (status: string) => {
    switch (status) {
      case 'active': return 'from-success/10 to-teal/10';
      case 'paused': return 'from-warning/10 to-orange/10';
      case 'completed': return 'from-info/10 to-indigo/10';
      default: return 'from-muted/10 to-muted/20';
    }
  };

  const executedWeeks = cycle.weeks?.filter(week => week.status === 'executed').length;

  return (
    <div className={`bg-gradient-to-br ${getStatusGradient(cycle.status)} backdrop-blur-sm rounded-2xl border-2 ${getStatusColor(cycle.status).split(' ')[1]} p-6 shadow-lg`}>
      {/* Cycle Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className={`w-4 h-4 rounded-full ${getStatusColor(cycle.status).split(' ')[0]} shadow-lg`}></div>
          <div>
            <h3 className="text-2xl font-bold text-foreground mb-1">{cycle.name} <small className='font-normal text-sm'>({cycle?.full_name})</small></h3>
            <p className="text-muted-foreground">
              Total: ₹{Number(cycle.totalAmount).toFixed(2)} • Profit: {cycle.profit?.toFixed(2)}%
              {cycle.startDate && ` • Started: ${cycle.startDate}`}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Total Count Display */}
          <div className="flex items-center space-x-3 bg-gradient-to-r from-purple/10 to-pink/10 rounded-lg px-4 py-2 border border-purple/30">
            <Hash className="w-5 h-5 text-purple" />
            <span className="text-purple font-semibold">Total: {cycle.totalCount}</span>
          </div>
          
          {/* Executed Count */}
          <div className="flex items-center space-x-3 bg-gradient-to-r from-teal/10 to-success/10 rounded-lg px-4 py-2 border border-teal/30">
            <TrendingUp className="w-5 h-5 text-teal" />
            <span className="text-teal font-semibold">Executed: {executedWeeks}/5</span>
          </div>

          {/* Pause/Resume Button */}
          {cycle.status !== 'completed' && (
            <Button
              onClick={() => onToggleStatus(cycle.id)}
              disabled={isLoading}
              className={`${
                cycle.status === 'active'
                  ? 'bg-gradient-to-r from-warning to-orange hover:from-warning/90 hover:to-orange/90 text-warning-foreground'
                  : 'bg-gradient-to-r from-success to-teal hover:from-success/90 hover:to-teal/90 text-success-foreground'
              } font-semibold px-4 py-2 rounded-lg shadow-lg border-0 disabled:opacity-50`}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {cycle.status === 'active' ? 'Pausing...' : 'Resuming...'}
                </>
              ) : cycle.status === 'active' ? (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Resume
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-muted-foreground mb-2">
          <span>Progress</span>
          <span>{executedWeeks}/5 weeks completed</span>
        </div>
        <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
          <div 
            className="bg-gradient-to-r from-primary to-purple h-3 rounded-full transition-all duration-300"
            style={{ width: `${(executedWeeks / 5) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Weeks Grid */}
      <div className="grid grid-cols-5 gap-4">
        {cycle.weeks.map((week, index) => (
          <WeekCard
            key={week.id}
            week={week}
            onUpdate={(updates) => updateWeek(week.schedule_id, updates)}
            isDisabled={cycle.status === 'paused' || cycle.status === 'completed'}
          />
        ))}
      </div>
    </div>
  );
};
