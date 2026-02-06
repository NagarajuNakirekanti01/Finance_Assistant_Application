import React from 'react';
import { useQuery } from 'react-query';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Target,
  CreditCard,
  PiggyBank,
  AlertCircle,
  Calendar
} from 'lucide-react';

import { transactionService } from '../services/transactionService';
import { accountService } from '../services/accountService';
import DashboardCard from '../components/dashboard/DashboardCard';
import SpendingChart from '../components/charts/SpendingChart';
import RecentTransactions from '../components/dashboard/RecentTransactions';
import BudgetProgress from '../components/dashboard/BudgetProgress';
import LoadingSpinner from '../components/common/LoadingSpinner';

const DashboardPage: React.FC = () => {
  // Fetch dashboard data
  const { data: accounts, isLoading: accountsLoading } = useQuery(
    'accounts',
    accountService.getAccounts
  );

  const { data: transactions, isLoading: transactionsLoading } = useQuery(
    'recent-transactions',
    () => transactionService.getTransactions({ page: 1, size: 10 })
  );

  const { data: summary, isLoading: summaryLoading } = useQuery(
    'transaction-summary',
    transactionService.getTransactionSummary
  );

  const isLoading = accountsLoading || transactionsLoading || summaryLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Calculate total balance
  const totalBalance = accounts?.reduce((sum, account) => sum + account.current_balance, 0) || 0;
  
  // Calculate this month's income and expenses
  const thisMonthIncome = summary?.total_income || 0;
  const thisMonthExpenses = summary?.total_expenses || 0;
  const netIncome = thisMonthIncome - thisMonthExpenses;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Welcome back! Here's your financial overview.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
          <Calendar className="w-4 h-4" />
          <span>{new Date().toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}</span>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Total Balance"
          value={`$${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          icon={<DollarSign className="w-6 h-6" />}
          trend={netIncome > 0 ? 'up' : 'down'}
          trendValue={`${netIncome > 0 ? '+' : ''}$${Math.abs(netIncome).toLocaleString()}`}
          trendLabel="this month"
          color="blue"
        />

        <DashboardCard
          title="Monthly Income"
          value={`$${thisMonthIncome.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          icon={<TrendingUp className="w-6 h-6" />}
          trend="up"
          trendValue="+12.5%"
          trendLabel="vs last month"
          color="green"
        />

        <DashboardCard
          title="Monthly Expenses"
          value={`$${thisMonthExpenses.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          icon={<TrendingDown className="w-6 h-6" />}
          trend="down"
          trendValue="-5.2%"
          trendLabel="vs last month"
          color="red"
        />

        <DashboardCard
          title="Savings Goal"
          value="$2,500"
          icon={<Target className="w-6 h-6" />}
          trend="up"
          trendValue="68%"
          trendLabel="completed"
          color="purple"
        />
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Spending Chart */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Spending by Category
              </h2>
              <select className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <option>Last 30 days</option>
                <option>Last 3 months</option>
                <option>Last 6 months</option>
              </select>
            </div>
            <SpendingChart data={summary?.top_categories || []} />
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Transactions
            </h2>
            <a 
              href="/transactions" 
              className="text-blue-600 dark:text-blue-400 text-sm hover:underline"
            >
              View all
            </a>
          </div>
          <RecentTransactions transactions={transactions || []} />
        </div>
      </div>

      {/* Budget Progress and Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Budget Progress */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Budget Progress
            </h2>
            <a 
              href="/budgets" 
              className="text-blue-600 dark:text-blue-400 text-sm hover:underline"
            >
              Manage budgets
            </a>
          </div>
          <BudgetProgress />
        </div>

        {/* Financial Alerts */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Financial Alerts
            </h2>
            <AlertCircle className="w-5 h-5 text-orange-500" />
          </div>
          
          <div className="space-y-3">
            <div className="flex items-start space-x-3 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
              <div className="flex-shrink-0">
                <CreditCard className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-orange-800 dark:text-orange-200">
                  Credit Card Payment Due
                </p>
                <p className="text-xs text-orange-600 dark:text-orange-400">
                  $1,234.56 due in 3 days
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
              <div className="flex-shrink-0">
                <TrendingUp className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Budget Alert: Dining
                </p>
                <p className="text-xs text-yellow-600 dark:text-yellow-400">
                  85% of monthly budget used
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex-shrink-0">
                <PiggyBank className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  Savings Goal Progress
                </p>
                <p className="text-xs text-green-600 dark:text-green-400">
                  You're ahead of schedule! 🎉
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;