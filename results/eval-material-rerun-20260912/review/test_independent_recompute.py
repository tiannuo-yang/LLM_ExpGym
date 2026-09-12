import unittest
from independent_recompute import aggregate, expected_slots, gap_value, strict_max, strict_mean


class BoundaryTests(unittest.TestCase):
    def test_fixed_required_members(self):
        self.assertIsNone(strict_mean([100,100,100,None]))
        self.assertIsNone(strict_max([100,100,100,None]))
        self.assertEqual(strict_mean([100,100,100,0]),75)

    def test_gap_clipped_per_member_not_after_average(self):
        self.assertEqual(gap_value(.1,.2,.4),0)
        self.assertAlmostEqual(gap_value(.5,.2,.4),150)
        self.assertAlmostEqual(strict_mean([gap_value(.1,.2,.4),gap_value(.3,.2,.4)]),25)
        self.assertEqual(gap_value(strict_mean([.1,.3]),.2,.4),0)

    def test_registered_counts(self):
        self.assertEqual([len(expected_slots(x)) for x in ('deepseek','kimi','gpt','glm')],[249,27,27,66])

    def test_three_repeats_then_items(self):
        rows=[]
        for item,vals in [('A',[0,30,60]),('B',[90,90,90]),('C',[30,30,30])]:
            for seed,v in zip([2200,2204,2208],vals):
                rows.append(dict(model='gpt',scenario='tuning',regime='cost_moderate',strategy='poolact',item=item,seed=seed,
                    agents=4,valid_agents=4,score_complete=True,normal_model_missing=0,other_unknown_agents=0,empty_scored_agents=0,gap_mi=v))
        a=aggregate(rows)[0]
        self.assertEqual(a['value'],50)
        self.assertEqual((a['expected_items'],a['expected_pools'],a['repeats_per_item']),(3,9,3))
        rows[0]['gap_mi']=None
        self.assertIsNone(aggregate(rows)[0]['value'])


if __name__=='__main__':
    unittest.main()
