def get_daily_avoided_runtime(alpha,demand,demand_baseline):
    return alpha * (demand_baseline - demand)
