# Comfort Bubble simulation formulas

The browser uses a coarse finite-difference temperature model on a 32 × 22 grid. At 1×, simulated seconds match wall-clock seconds. The 4× and 20× modes advance the same equations faster using substeps of at most one simulated second.

## Open-air diffusion

For each non-wall cell `i` and its accessible north, south, east, and west neighbors:

```text
T_i(next) = T_i + 0.14 × (average(T_neighbors) - T_i)
```

Wall cells are excluded. Doors are open-air cells, so heat and cold mix efficiently through them.

## Exterior heat transfer

Only cells on or immediately beside the outer grid boundary exchange heat with outdoors:

```text
T_i(next) += k_envelope × (T_outdoor - T_i)
k_envelope = 0.004 at the boundary
k_envelope = 0.001 one cell inside
```

Window cells add:

```text
T_i(next) += 0.045 × (T_outdoor - T_i)
```

Interior partitions never use outdoor temperature.

## Interior-wall conduction

Walls block airflow but conduct a small amount between opposite fluid cells:

```text
q = 0.004 × (T_side_B - T_side_A)
T_side_A(next) += q
T_side_B(next) -= q
```

## AC cooling and airflow

An AC is strictly ON or OFF, but it modulates its supply-air temperature from 15.5°C to 19.5°C according to avatar comfort error:

```text
T_supply = clamp(19.5 - 1.35 × max(0, T_avatar - T_comfort), 15.5, 19.5)
```

For downstream distance `d` and sideways offset `s` within a 16-cell plume:

```text
influence(d,s) = 0.045 × exp(-d / 7.5) × exp(-abs(s) / (1.8 + 0.06d))
T_i(next) += influence(d,s) × (T_supply - T_i)
T_i(next) += 0.09 × (T_upstream - T_i)
T_i(next) += 0.055 × (average(T_lateral) - T_i)
```

The direct plume stops at a wall. Diffusion carries cooling throughout connected open air, doors mix efficiently, and wall conduction slowly affects closed rooms.

## Stove heat

Within five cells of an active stove:

```text
T_i(next) += 0.035 × exp(-distance / 2.2)
```

## Thermostat decision

The selected control mode uses either avatar temperature or wall-thermostat temperature to produce a short-horizon forecast:

```text
T_control = T_avatar in Comfort Bubble mode
T_control = T_wall_thermostat in Traditional mode
trend = 0.94 × previous_trend + 0.06 × d(T_control)/dt
predicted = T_control + 60 × trend - residual_cooling

if AC is OFF and predicted > comfort_target + 0.45: turn AC ON
if AC is ON  and predicted <= comfort_target + 0.05: turn AC OFF early
otherwise: keep the previous state
```

The toggle selects which temperature controls the identical AC and prediction model.
