from optimization import ml_ranker
from optimization.optimizer import generate_plan, ENHANCED_STRATEGIES
from scripts.train_strategy_model import scenario
from optimization.validation import validate_plan

def test_model_inference_controls_strategy_order():
    lorry,boxes=scenario(84)
    expected,used=ml_ranker.rank_strategies(lorry,boxes,ENHANCED_STRATEGIES)
    assert used
    result=generate_plan(lorry,boxes)
    assert result['success']
    assert result['metrics']['ml_inference_used']
    assert result['metrics']['first_search_strategy']==list(expected[0])
    assert validate_plan(result['placements'],lorry,sum(b['loaded_weight'] for b in boxes),expected_boxes=boxes)[0]

def test_missing_model_falls_back(monkeypatch,tmp_path):
    ml_ranker.load_model.cache_clear()
    monkeypatch.setattr(ml_ranker,'MODEL_PATH',tmp_path/'missing.json')
    lorry,boxes=scenario(84)
    result=generate_plan(lorry,boxes)
    assert result['success']
    assert not result['metrics']['ml_inference_used']
    assert validate_plan(result['placements'],lorry,sum(b['loaded_weight'] for b in boxes),expected_boxes=boxes)[0]
    ml_ranker.load_model.cache_clear()

def test_corrupt_model_falls_back(monkeypatch):
    monkeypatch.setattr(ml_ranker,'load_model',lambda: {'version':1})
    lorry,boxes=scenario(84)
    assert ml_ranker.rank_strategies(lorry,boxes,ENHANCED_STRATEGIES)==(list(ENHANCED_STRATEGIES),False)
