"""Portfolio layer: strategies as target weights, a situation-aware blender, a risk overlay and an executor.

Flow (the same in research and in paper trading):

    Panel (prices known at each close)
      -> sleeves: each strategy's target weights per asset (longs and capped shorts)
      -> situation features (market state + AI/power theme), all point in time
      -> blender: how much of each sleeve to run in this situation (hybrids are weighted mixes)
      -> risk overlay: volatility target, per-asset / crypto / short caps, drawdown control (25% hard limit)
      -> executor: trade the difference between target and current holdings

Weights decided after the close of day t are traded at the next open (stocks) or the next UTC day's first price
(crypto); nothing in a decision uses a price from after the decision.
"""
