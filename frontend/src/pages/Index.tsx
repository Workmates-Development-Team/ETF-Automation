import React, { useEffect, useState } from 'react';
import { Plus, TrendingUp, Activity, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { CycleCard } from '@/components/CycleCard';
import { AddCycleForm } from '@/components/AddCycleForm';
import Header from '@/components/Header';

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
  updates: any;
  id: string;
  name: string;
  totalAmount: number;
  totalQty: number;
  profit: number;
  status: 'active' | 'paused' | 'completed';
  weeks: Week[];
  totalCount: number;
  startDate: string;
}

const Index = () => {
  const [cycles, setCycles] = useState<Cycle[]>([
    
  ]);

  
  const [loading, setLoading] = useState(false);

  async function getInitialCycles() {
    setLoading(true);
    try {
      const response = await fetch('https://etf-backend.codecatalystworks.com/api/all_etf_details');
      if (!response.ok) {
        throw new Error('Failed to fetch ETF details');
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching ETF details:', error);
      return null;
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    getInitialCycles().then(data => {
      if (data && Array.isArray(data)) {
      setCycles(data);
      }
    });
  }, [])

  const [showAddForm, setShowAddForm] = useState(false);
  const addNewCycle = async (name: string, amount: number, startDate: Date) => {
    const weekAmount = amount / 5;
    const newCycle: Cycle = {
      id: Date.now().toString(),
      name,
      totalAmount: amount,
      totalQty: 0,
      profit: 0.00,
      status: 'active',
      totalCount: 0,
      startDate: startDate.toLocaleDateString('en-GB'),
      weeks: Array.from({ length: 5 }, (_, index) => ({
        id: `${Date.now()}-${index + 1}`,
        weekNumber: index + 1,
        amount: weekAmount,
        date: new Date(startDate.getTime() + (index * 7 * 24 * 60 * 60 * 1000)).toLocaleDateString('en-GB'),
        ltp: 93.00,
        qty: 0,
        status: index === 0 ? 'active' : 'inactive' as 'executed' | 'active' | 'inactive'
      })),
      updates: undefined
    };

    // Call backend API to schedule ETF
    try {
      await fetch('https://etf-backend.codecatalystworks.com/api/schedule_etf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          total_amount: amount,
          etf_name: name,
          start_date: startDate.toISOString().slice(0, 10)
        })
      });
    } catch (error) {
      console.error('Failed to schedule ETF:', error);
    }

    setCycles(prev => [...prev, newCycle]);
    setShowAddForm(false);
  };


  const updateCycle = async (updatedCycle: Cycle) => {
    console.log(updatedCycle)
    // Call backend API to update the cycle
    setLoading(true);
    try {
      await fetch('https://etf-backend.codecatalystworks.com/api/update_schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schedule_id: updatedCycle.id,
          amount: updatedCycle.updates.amount,
          execution_date: updatedCycle.updates.date.split('/').reverse().join('-'), // Convert DD/MM/YYYY to YYYY-MM-DD
          execution_time: "15:36:00" 
        })
      });
    } catch (error) {
      console.error('Failed to update schedule:', error);
    } finally {
      setLoading(false);}

    // setCycles(prev => prev.map(cycle => 
    //   cycle.id === updatedCycle.id ? updatedCycle : cycle
    // ));

     getInitialCycles().then(data => {
      if (data && Array.isArray(data)) {
      setCycles(data);
      }
    });
  };
  
  const toggleCycleStatus = async (cycleId: string) => {
    const cycle = cycles.find(c => c.id === cycleId);
    if (!cycle) return;

    const isPausing = cycle.status === 'active';
    const endpoint = isPausing
      ? 'https://etf-backend.codecatalystworks.com/api/pause_cycle'
      : 'https://etf-backend.codecatalystworks.com/api/resume_cycle';

    try {
      await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: cycleId }),
      });
      // Optionally, refresh from backend:
      getInitialCycles().then(data => {
        if (data && Array.isArray(data)) {
          setCycles(data);
        }
      });
    } catch (error) {
      console.error('Failed to toggle cycle status:', error);
    }
  };

  const filterCycles = (status: string) => {
    if (status === 'all') return cycles;
    return cycles.filter(cycle => cycle.status === status);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-success';
      case 'paused': return 'bg-warning';
      case 'completed': return 'bg-info';
      default: return 'bg-muted';
    }
  };

  const getStatusCounts = () => {
    return {
      all: cycles.length,
      active: cycles.filter(c => c.status === 'active').length,
      paused: cycles.filter(c => c.status === 'paused').length,
      completed: cycles.filter(c => c.status === 'completed').length
    };
  };

  const statusCounts = getStatusCounts();

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="relative z-10 p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              {/* <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-purple to-pink bg-clip-text text-transparent mb-2">
                ETF Strategy Management
              </h1> */}
              <p className="text-muted-foreground text-lg">Advanced trading cycle automation</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-gradient-to-r from-success/10 to-success/20 backdrop-blur-sm rounded-lg px-4 py-2 border border-success/30">
                <Activity className="w-5 h-5 text-success" />
                <span className="text-success font-medium">{statusCounts.active} Active</span>
              </div>
              <div className="flex items-center space-x-2 bg-gradient-to-r from-primary/10 to-primary/20 backdrop-blur-sm rounded-lg px-4 py-2 border border-primary/30">
                <TrendingUp className="w-5 h-5 text-primary" />
                <span className="text-primary font-medium">
                  ₹{cycles.reduce((sum, c) => sum + Number(c.totalAmount), 0).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Add New Cycle Button */}
          <div className="flex justify-end mb-6">
            <Button
              onClick={() => setShowAddForm(true)}
              className="bg-gradient-to-r from-primary to-purple hover:from-primary/90 hover:to-purple/90 text-primary-foreground font-semibold px-6 py-3 rounded-lg shadow-lg border-0"
            >
              <Plus className="w-5 h-5 mr-2" />
              Add New Cycle
            </Button>
          </div>
        </div>

        {/* Add Cycle Form */}
        {showAddForm && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <AddCycleForm
              onSubmit={addNewCycle}
              onCancel={() => setShowAddForm(false)}
            />
          </div>
        )}

        {
          loading ? (
            <div className="flex items-center justify-center py-20">
              <Zap className="animate-spin w-16 h-16 text-primary" />
            </div>
          ): (
<div className="mb-8">
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-4 bg-card border border-border rounded-lg p-1">
              <TabsTrigger 
                value="all"
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo data-[state=active]:to-purple data-[state=active]:text-white rounded-md transition-all"
              >
                All ({statusCounts.all})
              </TabsTrigger>
              <TabsTrigger 
                value="active"
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-success data-[state=active]:to-teal data-[state=active]:text-white rounded-md transition-all"
              >
                Active ({statusCounts.active})
              </TabsTrigger>
              <TabsTrigger 
                value="paused"
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-warning data-[state=active]:to-orange data-[state=active]:text-white rounded-md transition-all"
              >
                Paused ({statusCounts.paused})
              </TabsTrigger>
              <TabsTrigger 
                value="completed"
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-info data-[state=active]:to-indigo data-[state=active]:text-white rounded-md transition-all"
              >
                Completed ({statusCounts.completed})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-6">
              <div className="space-y-6">
                {filterCycles('all').map((cycle) => (
                  <CycleCard
                    key={cycle.id}
                    cycle={cycle}
                    onUpdate={updateCycle}
                    onToggleStatus={toggleCycleStatus}
                  />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="active" className="mt-6">
              <div className="space-y-6">
                {filterCycles('active').map((cycle) => (
                  <CycleCard
                    key={cycle.id}
                    cycle={cycle}
                    onUpdate={updateCycle}
                    onToggleStatus={toggleCycleStatus}
                  />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="paused" className="mt-6">
              <div className="space-y-6">
                {filterCycles('paused').map((cycle) => (
                  <CycleCard
                    key={cycle.id}
                    cycle={cycle}
                    onUpdate={updateCycle}
                    onToggleStatus={toggleCycleStatus}
                  />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="completed" className="mt-6">
              <div className="space-y-6">
                {filterCycles('completed').map((cycle) => (
                  <CycleCard
                    key={cycle.id}
                    cycle={cycle}
                    onUpdate={updateCycle}
                    onToggleStatus={toggleCycleStatus}
                  />
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </div>
          )
        }

        {/* Filter Tabs */}
        

        {!loading && cycles.length === 0 && (
          <div className="text-center py-20">
            <div className="w-16 h-16 bg-gradient-to-r from-primary to-purple rounded-full flex items-center justify-center mx-auto mb-4">
              <Zap className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">No cycles yet</h3>
            <p className="text-muted-foreground">Create your first trading cycle to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;
