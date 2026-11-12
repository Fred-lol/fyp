-- The rear loading gate is represented by X=0.  Preserve a physically
-- executable sequence for existing plans: the deepest boxes load first and
-- each later step moves monotonically back toward the gate.
WITH gate_order AS (
    SELECT placement_id,
           ROW_NUMBER() OVER (
               PARTITION BY plan_id
               ORDER BY x DESC, z ASC, y ASC, order_id ASC, box_instance ASC, placement_id ASC
           ) AS loading_sequence
    FROM box_placements
)
UPDATE box_placements AS placement
SET sequence_number = gate_order.loading_sequence
FROM gate_order
WHERE placement.placement_id = gate_order.placement_id;
