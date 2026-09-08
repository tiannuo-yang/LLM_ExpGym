#!/usr/bin/env python3
import unittest
import metadata_completion as m


class MetadataFixtures(unittest.TestCase):
    def row(self,classification='closed_original_pool'):
        return {'job_id':'synthetic','classification':classification,'guarded_skips':1,
                'original_status_passed':True,'infra_qualified':True,'performance_qualified':True,
                'abort_observed':False,'retained_semantic_zero_count':0,'reasons':[]}

    def test_unstarted_missing_is_not_zero(self):
        row=self.row('no_execution_evidence_observed');del row['retained_semantic_zero_count']
        self.assertEqual(m.pool_rows_for_csv([row])[0]['retained_semantic_zero_count'],'not_applicable_no_execution')

    def test_started_missing_is_rejected(self):
        row=self.row();del row['retained_semantic_zero_count']
        with self.assertRaises(m.c.DeliveryError):m.pool_rows_for_csv([row])

    def test_real_original_zero_is_retained(self):
        self.assertEqual(m.pool_rows_for_csv([self.row()])[0]['retained_semantic_zero_count'],0)

    def test_unknown_remains_unknown(self):
        row=self.row();row['original_status_passed']=None
        self.assertEqual(m.pool_rows_for_csv([row])[0]['original_status_passed'],'unknown')

    def test_other_missing_required_field_rejected(self):
        row=self.row();del row['job_id']
        with self.assertRaises(KeyError):m.pool_rows_for_csv([row])


if __name__=='__main__':unittest.main(verbosity=2)
