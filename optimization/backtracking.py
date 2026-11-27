"""Bounded beam backtracking over box order, legal rotation and face positions."""
from time import perf_counter
from optimization.constraints import orientations, fully_supported, stack_loads_valid
from optimization.validation import inside_lorry, boxes_overlap, validate_plan


def repack(lorry, boxes, score, deadline, beam_width=12):
    # Import at call time because the shared optimizer invokes this search.
    from optimization.optimizer import _make_placement, _finalise_deep_loading_sequence
    beam = [([], tuple(range(len(boxes))))]
    stats = {'backtracking_nodes': 0, 'backtracking_complete': 0}
    complete = []
    if perf_counter() >= deadline:
        return complete, stats
    for depth in range(len(boxes)):
        children = []
        for placed,remaining in beam:
            types = set()
            for index in remaining:
                b=boxes[index]
                shape=tuple(float(b[k]) for k in ('length','width','height','loaded_weight'))
                if shape in types:
                    continue
                types.add(shape)
                for dims in orientations(b['length'],b['width'],b['height']):
                    l,w,h=dims
                    xs,ys,zs={0.0},{0.0},{0.0}
                    for p in placed:
                        for face in (p['x'],p['x']+p['placed_length']): xs.update((face,face-l))
                        for face in (p['y'],p['y']+p['placed_width']): ys.update((face,face-w))
                        zs.add(p['z']+p['placed_height'])
                    for z in sorted(zs):
                        for x in sorted(v for v in xs if 0<=v<=float(lorry['internal_length'])-l+1e-7):
                            for y in sorted(v for v in ys if 0<=v<=float(lorry['internal_width'])-w+1e-7):
                                if perf_counter()>=deadline:
                                    return complete,stats
                                p=_make_placement(b,(x,y,z),dims)
                                if not inside_lorry(p,lorry) or any(boxes_overlap(p,o) for o in placed) or not fully_supported(p,placed): continue
                                trial=[*placed,p]
                                if not stack_loads_valid(trial): continue
                                stats['backtracking_nodes']+=1
                                rest=tuple(i for i in remaining if i!=index)
                                if not rest:
                                    final=[dict(p) for p in trial]
                                    _finalise_deep_loading_sequence(final,lorry)
                                    if validate_plan(final,lorry,sum(float(b['loaded_weight']) for b in boxes),expected_boxes=boxes)[0]:
                                        complete.append(final)
                                        stats['backtracking_complete']+=1
                                else:
                                    # Keep alternative partial arrangements ranked by geometry.
                                    quality=score(trial,lorry)
                                    children.append((quality,trial,rest))
        if complete:
            return complete,stats
        children.sort(key=lambda c:c[0])
        beam=[]; seen=set()
        for _,trial,rest in children:
            signature=(tuple(sorted((p['x'],p['y'],p['z'],p['placed_length'],p['placed_width'],p['placed_height'],p['loaded_weight']) for p in trial)),rest)
            if signature not in seen:
                seen.add(signature); beam.append((trial,rest))
            if len(beam)>=beam_width: break
        if not beam: break
    return complete,stats
