import unittest
from optimization.optimizer import generate_plan
from optimization.validation import validate_plan

class OptimizerTests(unittest.TestCase):
    def test_valid_small_plan(self):
        lorry={"internal_length":200.0,"internal_width":100.0,"internal_height":100.0,"max_weight":500.0}
        boxes=[]
        for i in range(3):
            boxes.append({"order_id":1,"box_profile_id":1,"box_instance":i+1,"box_name":"Test Box","length":50.0,"width":40.0,"height":30.0,"loaded_weight":20.0})
        result=generate_plan(lorry,boxes)
        self.assertTrue(result["success"],result.get("message"))
        ok,errors=validate_plan(result["placements"],lorry,60.0)
        self.assertTrue(ok,errors)

    def test_weight_failure(self):
        lorry={"internal_length":200.0,"internal_width":100.0,"internal_height":100.0,"max_weight":10.0}
        boxes=[{"order_id":1,"box_profile_id":1,"box_instance":1,"box_name":"Heavy","length":50.0,"width":40.0,"height":30.0,"loaded_weight":20.0}]
        result=generate_plan(lorry,boxes)
        self.assertFalse(result["success"])

if __name__ == "__main__": unittest.main()
