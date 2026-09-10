"""Independent bounded CPU peer; only source/control metadata and synthetic payloads."""
import ast, collections, contextlib, hashlib, importlib.util, io, json
from pathlib import Path
import tempfile, unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
P = HERE.parent
NEW = P / "k3_union_remote_restore_candidate_v2"
OLD = P / "glm_full_remote_restore_candidate_v1/verify_restored_files.py"
V1 = P / "k3_union_remote_restore_candidate_v1/verify_restored_files.py"
PINS = {
 OLD: "40e7b3af4e1d4b1e573e60ee192de19f6db9bd223515b32acbe0c8e345bc7d2b",
 V1: "07095c86098698ece378c7cb39d657b2a600d42ae5fd99cfb0bc68f57c72311b",
 NEW/"verify_restored_files.py": "80f35ba87e127d13a73daf958f7fc3d44f0f07a34aab2c512eaedd485b14866e",
 NEW/"test_verify_restored_files.py": "573d99b01395255dc157a5ea7b4e0eb92cd0d2df309df565dd7155f269948698",
}
for path,pin in PINS.items():
 assert hashlib.sha256(path.read_bytes()).hexdigest()==pin
spec=importlib.util.spec_from_file_location("owner_fake_fixture_only",NEW/"test_verify_restored_files.py")
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
m=fixture.m
DETAILS={}

class Peer(unittest.TestCase):
 def fake(self):
  temp=tempfile.TemporaryDirectory(prefix="synthetic_",dir=HERE)
  self.addCleanup(temp.cleanup)
  f=fixture.Fake(Path(temp.name));self.addCleanup(f.close);return f
 def reject(self,f,expected):
  with self.assertRaisesRegex(RuntimeError,expected):f.run()
  self.assertFalse(f.args.output_receipt.exists())
 def test_1_static_core_scope_and_entry_contract(self):
  oldtext=OLD.read_text();newtext=(NEW/"verify_restored_files.py").read_text()
  oldtree=ast.parse(oldtext);newtree=ast.parse(newtext)
  funcs=lambda tree:{n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
  old,new=funcs(oldtree),funcs(newtree)
  helpers=("need","encoded","signature","path_safe","digest","load","relative","tree")
  for name in helpers:
   self.assertEqual(ast.dump(old[name]),ast.dump(new[name]))
   self.assertEqual(ast.get_source_segment(oldtext,old[name]),ast.get_source_segment(newtext,new[name]))
  def loop(f):
   found=[n for n in f.body if isinstance(n,ast.For) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="source_index" for t in x.targets) for x in n.body)]
   self.assertEqual(len(found),1);return found[0]
  a,b=loop(old["main"]),loop(new["main"])
  self.assertEqual(ast.dump(a),ast.dump(b))
  self.assertEqual(ast.get_source_segment(oldtext,a),ast.get_source_segment(newtext,b))
  self.assertEqual(ast.dump(old["cli"]),ast.dump(new["cli"]))
  # The complete suffix includes owner/global/COMPLETE/pathset/final rehash/output checks.
  self.assertEqual([ast.dump(x) for x in old["main"].body[old["main"].body.index(a):]],
                   [ast.dump(x) for x in new["main"].body[new["main"].body.index(b):]])
  self.assertEqual(len(old["main"].body),len(new["main"].body))
  diffs=[(x.lineno,y.lineno,type(x).__name__) for x,y in zip(old["main"].body,new["main"].body) if ast.dump(x)!=ast.dump(y)]
  self.assertEqual([x[2] for x in diffs],["Assign","Expr","For","Assign"])
  self.assertEqual(newtext,V1.read_text().replace("(36, 66644, 1751139153)","(36, 66643, 1751137861)").replace("(467, 195086721)","(466, 195085429)"))
  self.assertEqual(m.TOTALS,(36,66643,1751137861))
  self.assertEqual(m.RAW_TOTALS,(65260,1303033772))
  self.assertEqual(m.CONTROL_TOTALS,{"controls":(917,253018660),"recovery-controls-000001":(466,195085429)})
  self.assertEqual(set(m.RAW_COUNTS),{"batch-%06d"%i for i in range(1,34)}|{"recovery-raw-000001"})
  self.assertEqual(sum(m.RAW_COUNTS.values()),65260)
  self.assertEqual(set(m.RAW_CATEGORIES),set(m.RAW_COUNTS))
  self.assertEqual(set(m.CONTROL_CATEGORIES),set(m.CONTROL_TOTALS))
  with patch("sys.argv",["verify","--file-count","1"]),contextlib.redirect_stderr(io.StringIO()):
   with self.assertRaises(SystemExit) as e:m.cli()
  self.assertEqual(e.exception.code,2)
  DETAILS["static"]={"helpers_text_AST":8,"member_loop_and_whole_suffix_AST_same":True,"CLI_AST_same":True,"changed_main_statements_old_new":diffs,"v1_to_v2_exact_two_literals":True,"scope_fixed":[36,66643,1751137861]}
 def test_2_scope_rejections_then_complete36_digest_once(self):
  f=self.fake()
  f.exit_record["actual_exit_code"]=False
  f.args.cli_exit_sha256=fixture.put(f.args.cli_exit,f.exit_record)
  self.reject(f,"cli_not_success")
  f.exit_record["actual_exit_code"]=0
  f.args.cli_exit_sha256=fixture.put(f.args.cli_exit,f.exit_record)
  row=f.row(fixture.NEW_CONTROLS);category=row["category"]
  row["category"]="recovery-raw";f.bind_collection_change()
  self.reject(f,"public_controls_scope")
  row["category"]=category;f.bind_collection_change()
  row["file_count"]=True;f.bind_collection_change()
  self.reject(f,"exact_member_counts")
  row["file_count"]=1;f.bind_collection_change()
  # Trap stale default entrypoints without changing the correct union.
  fixture.put(f.release/"payload/collection/INDEX.json",{"invalid_old_default":True})
  before={str(p):p.read_bytes() for root in (f.release,f.output) for p in root.rglob("*") if p.is_file()}
  payloads={f.output/bid/"payload"/("workspace/f%03d.bin"%i) for i,bid in enumerate(f.bids)}
  calls=collections.Counter();original=m.digest
  def count(path,*args,**kwargs):
   if path in payloads:calls[str(path)]+=1
   return original(path,*args,**kwargs)
  with patch.object(m,"digest",count):f.run()
  self.assertEqual(set(calls),{str(x) for x in payloads})
  self.assertTrue(all(c==1 for c in calls.values()))
  self.assertEqual(before,{p:Path(p).read_bytes() for p in before})
  out=json.loads(f.args.output_receipt.read_bytes())
  self.assertTrue(out["passed"]);self.assertEqual((out["bundle_count"],out["file_count"],out["original_bytes"]),(36,36,36))
  self.assertTrue(out["incomplete_absent"]);self.assertTrue(out["exact_output_file_set"])
  DETAILS["fake36"]={"original_paths_hashed_once":len(calls),"input_bytes_unchanged":True,"boolean_exit_category_boolean_count_rejected":True,"stale_default_ignored":True}
 def test_3_midstream_root_proof_change_cannot_commit_success(self):
  f=self.fake();first=f.output/f.bids[0]/"payload/workspace/f000.bin"
  original=m.digest;changed=[]
  def mutate(path,*args,**kwargs):
   out=original(path,*args,**kwargs)
   if path==first and not changed:
    fixture.put(f.args.root_remote_proof,{"synthetic_only":True,"changed_during_verification":True})
    changed.append(True)
   return out
  with patch.object(m,"digest",mutate):self.reject(f,"metadata_changed_after")
  self.assertEqual(changed,[True])
  DETAILS["midstream"]={"root_proof_changed_after_first_synthetic_payload":True,"rejected_by_final_metadata_hash":True,"success_receipt_absent":True}

if __name__=="__main__":
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Peer))
 print(json.dumps({"synthetic_only":True,"tests":result.testsRun,"passed":result.wasSuccessful(),"details":DETAILS},sort_keys=True))
 raise SystemExit(0 if result.wasSuccessful() else 1)

