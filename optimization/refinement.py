"""Bounded, monotonic refinement of already validated physical placements."""
from time import perf_counter
from optimization.constraints import orientations, loading_sequence_key, fully_supported
from optimization.validation import validate_plan, inside_lorry, boxes_overlap


def _sequence(placements):
    result = sorted((dict(p) for p in placements), key=loading_sequence_key)
    for index, p in enumerate(result, 1):
        p["sequence_number"] = index
    return result


def refine_plan(placements, lorry, boxes, score, deadline, protected_metrics):
    """Try face-aligned relocation/rotation; never mutate or degrade input.

    All trials use original box dimensions. Revalidating the entire layout
    prevents moving a support out from under another box. The independent
    validator also checks the new loading sequence and cumulative stack load.
    """
    total = sum(float(b["loaded_weight"]) for b in boxes)
    current = _sequence(placements)
    if not validate_plan(current, lorry, total, expected_boxes=boxes)[0]:
        raise ValueError("Refinement requires a complete validated arrangement")
    identity = lambda p: (int(p["order_id"]), int(p["box_profile_id"]), int(p["box_instance"]))
    required = {identity(b): b for b in boxes}
    current_score = score(current, lorry)
    limits = protected_metrics(current, lorry)
    stats = {"refinement_trials": 0, "refinement_moves": 0}
    for sweep in range(3):
        improved = False
        # Repack pairs jointly: a single-box descent can get stuck when
        # both footprints must rotate together to form a shorter group.
        ids = [identity(p) for p in current if p["z"] <= 1e-7]
        for ai, aid in enumerate(ids):
            for bid in ids[ai+1:]:
                if perf_counter() >= deadline:
                    return current, stats
                a = next(p for p in current if identity(p)==aid)
                b = next(p for p in current if identity(p)==bid)
                others = [p for p in current if identity(p) not in (aid,bid)]
                end = max(a["x"]+a["placed_length"],b["x"]+b["placed_length"])
                y = min(a["y"],b["y"])
                best, best_score = current, current_score
                for first,second in ((a,b),(b,a)):
                    ra,rb=required[identity(first)],required[identity(second)]
                    for la,wa,ha in orientations(ra["length"],ra["width"],ra["height"]):
                        for lb,wb,hb in orientations(rb["length"],rb["width"],rb["height"]):
                            for side_by_side in (True,False):
                                if perf_counter() >= deadline:
                                    return current,stats
                                pa=dict(first,x=end-la,y=y,z=0.,placed_length=la,placed_width=wa,placed_height=ha,orientation=f"{la:g} x {wa:g} x {ha:g}")
                                pb=dict(second,x=end-lb if side_by_side else end-la-lb,y=y+wa if side_by_side else y,z=0.,placed_length=lb,placed_width=wb,placed_height=hb,orientation=f"{lb:g} x {wb:g} x {hb:g}")
                                if any(not inside_lorry(p,lorry) or any(boxes_overlap(p,o) for o in others) for p in (pa,pb)):
                                    continue
                                trial=_sequence([*others,pa,pb])
                                trial_score=score(trial,lorry)
                                if trial_score>=best_score or trial_score[:5]>=current_score[:5] or any(v>limit+1e-7 for v,limit in zip(protected_metrics(trial,lorry),limits)):
                                    continue
                                stats["refinement_trials"]+=1
                                if validate_plan(trial,lorry,total,expected_boxes=boxes)[0]:
                                    best,best_score=trial,trial_score
                if best_score<current_score:
                    current,current_score=best,best_score
                    limits=protected_metrics(current,lorry)
                    stats["refinement_moves"]+=1
                    improved=True
        # Smaller/upper boxes first can free floor gaps without disturbing bases.
        order = sorted(current, key=lambda p: (-p["z"],p["placed_length"]*p["placed_width"],identity(p)))
        for original in order:
            if perf_counter() >= deadline:
                return current, stats
            item = next(p for p in current if identity(p)==identity(original))
            others = [p for p in current if identity(p)!=identity(item)]
            box = required[identity(item)]
            best, best_score = current, current_score
            for length,width,height in orientations(box["length"],box["width"],box["height"]):
                xs = {0.,float(lorry["internal_length"])-length,item["x"]}
                ys = {0.,float(lorry["internal_width"])-width,item["y"]}
                zs = {0.,item["z"]}
                for other in others:
                    for face in (other["x"],other["x"]+other["placed_length"]):
                        xs.update((face,face-length))
                    for face in (other["y"],other["y"]+other["placed_width"]):
                        ys.update((face,face-width))
                    zs.add(other["z"]+other["placed_height"])
                for z in sorted(zs):
                    for x in sorted(xs,reverse=True):
                        for y in sorted(ys):
                            if perf_counter() >= deadline:
                                return current, stats
                            candidate=dict(item,x=x,y=y,z=z,placed_length=length,placed_width=width,placed_height=height,orientation=f"{length:g} x {width:g} x {height:g}")
                            if not inside_lorry(candidate,lorry) or any(boxes_overlap(candidate,p) for p in others) or not fully_supported(candidate,others):
                                continue
                            trial=_sequence([*others,candidate])
                            trial_score=score(trial,lorry)
                            if any(value > limit + 1e-7 for value, limit in zip(protected_metrics(trial, lorry), limits)):
                                continue
                            if trial_score >= best_score or trial_score[:5] >= current_score[:5]:
                                continue
                            stats["refinement_trials"] += 1
                            if validate_plan(trial,lorry,total,expected_boxes=boxes)[0]:
                                best,best_score=trial,trial_score
            if best_score < current_score:
                current,current_score=best,best_score
                limits=protected_metrics(current, lorry)
                stats["refinement_moves"] += 1
                improved=True
        if not improved:
            break
    return current,stats
