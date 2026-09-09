"""Copy ROOT-selected 33 K3 raw bundles plus one controls bundle; no pack/restore."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys

PUB = Path(__file__).resolve().parent.parent
RAW_ROOT = PUB / 'k3_formal_original_local_delivery_v2'
RAW_COUNTS = {'batch-%06d' % i: 2000 if i < 33 else 188 for i in range(1, 34)}
RAW_TOTALS, CONTROL_TOTALS = (64188, 1268512973), (917, 253018660)
TOTALS = (34, 65105, 1521531633)
PINS = {'collection_restore_candidate_v2/restore_collection.py':'24a2ff6da7521c7920ce50ea7491aa682310e78874ba2d552649e9d2d88bb6b2',
        'shard_delivery_candidate_v2/common.py':'7147524d5799dc1264f088518db19251c5f906bc2da501854ce279f56d73263e',
        'shard_delivery_candidate_v2/restore.py':'ec20a0e22c8f810b09e894e0ddc6cc8dec114a66be4fe23cab8a55f3b62ac710',
        'shard_delivery_candidate_v2/pack.py':'07eb7a20e838ca53bfda6144887283e597914e95fb11c5e16ff43f95f09f5f10',
        'validate_bundle_v2.py':'aea61a9309cb6069240b90e0ca706403b0f21b3e7f77a2f88d462e6ba8734116'}


def need(value, code):
    if not value:
        raise ValueError(code)


def read_ref(ref, c, inputs):
    need(type(ref) is dict and set(ref)=={'path','sha256','bytes'}, 'external_ref_schema')
    p=Path(ref['path'])
    need(p.is_absolute() and str(p)==ref['path'], 'absolute_ref_path')
    c.number(ref['bytes'],c.INDEX_LIMIT,'metadata_ref_bytes')
    c.checksum(ref['sha256']); c.lexical(p)
    value,raw=c.load_json(p,ref['sha256'])
    need(len(raw)==ref['bytes'],'metadata_ref_size')
    for old,digest in inputs:
        need(old!=p or digest==ref['sha256'],'conflicting_input_pin')
    if (p,ref['sha256']) not in inputs:
        inputs.append((p,ref['sha256']))
    return value


def select(selection, c, inputs):
    """ROOT's explicit proof projections; no discovery or guessed receipt adapters."""
    need(set(selection)=={'schema','issuer','original_execution_complete','original_score_complete',
        'bundle_count','file_count','original_bytes','bundles'}
        and selection['schema']=='root-k3-collection-selection-v1' and selection['issuer']=='ROOT'
        and selection['original_execution_complete'] is False and selection['original_score_complete'] is False
        and tuple(selection[k] for k in ('bundle_count','file_count','original_bytes'))==TOTALS,'root_selection_scope')
    need(type(selection['bundles']) is list and len(selection['bundles'])==TOTALS[0],'exact_bundle_count')
    selected,roots=[],{}
    for row in selection['bundles']:
        need(set(row)=={'bundle_id','category','bundle_root','index_ref','complete_ref','file_count','original_bytes',
            'operator_ref','local_proof_ref','local_verification'},'selected_row_schema')
        bid=row['bundle_id']; root=Path(row['bundle_root'])
        need(bid in RAW_COUNTS or bid=='controls','unknown_bundle_id')
        need(bid not in roots and root.is_absolute() and str(root)==row['bundle_root'],'duplicate_id_or_root_path')
        c.lexical(root)
        need(all(root!=p and p not in root.parents and root not in p.parents for p in roots.values()),'duplicate_nested_bundle_roots')
        roots[bid]=root
        expected_category='controls' if bid=='controls' else 'original-node-failure'
        need(row['category']==expected_category,'fixed_category')
        c.number(row['file_count'],c.MAX_SHARDS*c.MAX_FILES,'selected_file_count',1)
        c.number(row['original_bytes'],c.MAX_SHARDS*c.EXPANDED,'selected_original_bytes')
        if bid=='controls':
            need((row['file_count'],row['original_bytes'])==CONTROL_TOTALS,'controls_totals')
        else:
            need(root==RAW_ROOT/'batches'/bid/'bundle' and row['file_count']==RAW_COUNTS[bid],'fixed_raw_bundle_root_count')
        need(Path(row['index_ref']['path'])==root/'payload/INDEX.json'
            and Path(row['complete_ref']['path'])==root/'COMPLETE.json','selected_root_index_complete_binding')
        for key in ('index_ref','complete_ref','operator_ref','local_proof_ref'):
            need(type(read_ref(row[key],c,inputs)) is dict,'expected_metadata_object')
        proof=row['local_verification']
        need(set(proof)=={'pack_exit_code','restore_exit_code','complete_original_and_restored_path_bytes_sha_match',
            'all_started_children_reaped'} and type(proof['pack_exit_code']) is int and proof['pack_exit_code']==0
            and type(proof['restore_exit_code']) is int and proof['restore_exit_code']==0
            and proof['complete_original_and_restored_path_bytes_sha_match'] is True
            and proof['all_started_children_reaped'] is True,'root_local_proof_projection_not_passed')
        selected.append((bid,row['category'],row['index_ref'],row['complete_ref'],row['file_count'],row['original_bytes']))
    need(set(roots)==set(RAW_COUNTS)|{'controls'},'missing_bundle_id')
    raw=[r for r in selected if r[0]!='controls']
    need((sum(r[4] for r in raw),sum(r[5] for r in raw))==RAW_TOTALS,'raw_totals')
    need((len(selected),sum(r[4] for r in selected),sum(r[5] for r in selected))==TOTALS,'whole_collection_totals')
    return sorted(selected),roots


def assemble(go_path, go_sha256, output):
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    for name,digest in PINS.items():
        need(hashlib.sha256((PUB/name).read_bytes()).hexdigest()==digest,'frozen_tool_identity')
    wrapper_path=PUB/'collection_restore_candidate_v2/restore_collection.py'
    spec=importlib.util.spec_from_file_location('assembly_frozen_collection',wrapper_path)
    wrapper=importlib.util.module_from_spec(spec); spec.loader.exec_module(wrapper)
    c,_=wrapper.frozen_tools(); output=c.fresh(output); c.checksum(go_sha256)
    need(Path(go_path).is_absolute(),'absolute_go_path')
    go,go_raw=c.load_json(go_path,go_sha256)
    need(set(go)=={'schema','issuer','approved','action','assembler_sha256','selection_ref','output_dir',
        'publication_authorized','network_authorized'} and go['schema']=='root-k3-collection-assembly-go-v1'
        and go['issuer']=='ROOT' and go['approved'] is True and go['action']=='assemble_local_only'
        and go['output_dir']==str(output) and go['publication_authorized'] is False
        and go['network_authorized'] is False and c.sha(Path(__file__).read_bytes())==go['assembler_sha256'],'independent_root_assembly_go')
    inputs=[(Path(go_path),go_sha256)]
    selection=read_ref(go['selection_ref'],c,inputs)
    selected,selected_roots=select(selection,c,inputs)
    copies=[]; original_paths=set(); bundles=[]; metadata_bytes=0; protected=[]
    for bid,classification,index_ref,complete_ref,count,size in selected:
        index_path=c.lexical(index_ref['path']); root=index_path.parent.parent; protected.append(root)
        expected_root=selected_roots[bid]
        need(root==expected_root and index_path==root/'payload/INDEX.json' and Path(complete_ref['path'])==root/'COMPLETE.json','exact_bundle_root')
        index,index_raw=c.load_json(index_path,index_ref['sha256'])
        need(len(index_raw)==index_ref['bytes'] and c.verify_completion(root,{'kind':'bundle','index_sha256':index_ref['sha256']})==complete_ref['sha256'],'original_bundle_complete')
        expected_tree={'COMPLETE.json','payload/INDEX.json','payload/SOURCE_SCAN.json'}; originals=[]
        for n,shard in enumerate(index['shards'],1):
            page='indexes/part-%06d.json'%n; archive='shards/part-%06d.tar.gz'%n
            need(shard['index']==page and shard['archive']==archive,'canonical_shard_names')
            value,raw=c.load_json(root/'payload'/page,shard['index_sha256']); c.validate_rows(value['files'])
            need(len(raw)==shard['index_bytes'] and len(value['files'])==shard['file_count'],'member_page_binding')
            originals+=value['files']; expected_tree.update(('payload/'+page,'payload/'+archive))
        paths=[r['path'] for r in originals]
        need(len(set(paths))==len(paths) and not original_paths.intersection(paths),'duplicate_global_original')
        original_paths.update(paths)
        need((len(paths),sum(r['bytes'] for r in originals))==(count,size)==(index['file_count'],index['original_bytes']),'whole_original_counts')
        need(c.tree(root)==expected_tree,'bundle_extra_or_missing_file')
        for name in sorted(expected_tree):
            length,digest=c.stream_hash(root/name)
            copies.append((root/name,'collection/'+bid+'/'+name,length,digest))
            if name.endswith('.json'):
                metadata_bytes+=length
        bundles.append(dict(bundle_id=bid,category=classification,index=bid+'/payload/INDEX.json',sha256=index_ref['sha256'],file_count=count,original_bytes=size))
    c.no_path_prefixes(original_paths)
    collection=dict(schema='whole-file-collection-v1',bundle_count=TOTALS[0],file_count=TOTALS[1],original_bytes=TOTALS[2],bundles=bundles)
    collection_raw=c.encoded(collection); collection_sha=c.sha(collection_raw)
    need(metadata_bytes+len(collection_raw)<=wrapper.MAX_METADATA,'collection_metadata_limit')
    for name,digest in PINS.items():
        copies.append((PUB/name,'tools/publication/'+name,(PUB/name).stat().st_size,digest))
    need(all(output!=p and p not in output.parents and output not in p.parents for p in protected+[Path(__file__).parent,PUB/'shard_delivery_candidate_v2',PUB/'collection_restore_candidate_v2']+[p for p,_ in inputs]),'output_input_overlap')
    need(len({r[1] for r in copies})==len(copies),'duplicate_delivery_path')
    output.mkdir(mode=0o700)
    for source,name,length,digest in copies:
        target=output/c.relative(name); target.parent.mkdir(parents=True,exist_ok=True)
        with os.fdopen(os.open(c.lexical(source),os.O_RDONLY|os.O_NOFOLLOW),'rb') as reader, target.open('xb') as writer:
            observed=hashlib.sha256(); total=0
            for block in iter(lambda:reader.read(c.BLOCK),b''):
                total+=len(block); need(total<=length,'source_grew'); observed.update(block); writer.write(block)
            writer.flush(); os.fsync(writer.fileno())
        need((total,observed.hexdigest())==(length,digest) and c.stream_hash(source)==(length,digest)
             and c.stream_hash(target)==(length,digest),'whole_file_copy_mismatch')
    c.write_new(output/'collection/INDEX.json',collection_raw)
    wrapper.preflight(output/'collection/INDEX.json',collection_sha,c)
    for bid,_,index_ref,complete_ref,_,_ in selected:
        need(c.verify_completion(output/'collection'/bid,{'kind':'bundle','index_sha256':index_ref['sha256']})==complete_ref['sha256'],'copied_bundle_complete')
        need(c.verify_completion(Path(index_ref['path']).parent.parent,{'kind':'bundle','index_sha256':index_ref['sha256']})==complete_ref['sha256'],'original_bundle_changed_after_copy')
    for p,h in inputs:
        c.load_json(p,h)
    for name,digest in PINS.items():
        need(c.stream_hash(PUB/name)[1]==digest,'original_tool_changed_after_copy')
    rows=[dict(path=name,bytes=length,sha256=digest) for _,name,length,digest in copies]
    rows.append(dict(path='collection/INDEX.json',bytes=len(collection_raw),sha256=collection_sha)); rows.sort(key=lambda r:r['path'])
    for row in rows:
        need(c.stream_hash(output/row['path'])==(row['bytes'],row['sha256']),'final_delivery_file_changed')
    need(c.tree(output)=={r['path'] for r in rows},'delivery_unlisted_file')
    manifest=c.encoded(dict(schema='local-release-files-v1',files=rows,excludes_only=['RELEASE_FILES.json','ASSEMBLY_RECEIPT.json']))
    c.write_new(output/'RELEASE_FILES.json',manifest)
    need(c.sha(Path(__file__).read_bytes())==go['assembler_sha256'],'assembler_changed_after_copy')
    receipt=dict(schema='local-k3-34-bundle-assembly-v1',passed=True,bundle_count=TOTALS[0],file_count=TOTALS[1],original_bytes=TOTALS[2],
        collection_index_sha256=collection_sha,release_files_sha256=c.sha(manifest),release_payload_files=len(rows),
        input_refs=[dict(path=str(p),sha256=h) for p,h in inputs],tool_pins=PINS,assembler_sha256=c.sha(Path(__file__).read_bytes()),
        source_and_copied_bundle_bytes_sha_equal=True,global_original_paths_unique=True,metadata_bytes=metadata_bytes+len(collection_raw),
        new_pack_or_restore_calls=0,private_key_reads=0,local_only=True,publication_performed=False,remote_restore_performed=False,full_project_complete=False,
        original_execution_complete=False,original_score_complete=False,proof_projection_review='ROOT selection; source proof bytes pinned, no guessed upstream schema adapter')
    raw=c.encoded(receipt); c.write_new(output/'ASSEMBLY_RECEIPT.json',raw)
    need(c.tree(output)=={r['path'] for r in rows}|{'RELEASE_FILES.json','ASSEMBLY_RECEIPT.json'},'final_release_file_set')
    return dict(passed=True,collection_index_sha256=collection_sha,assembly_receipt_sha256=c.sha(raw),release_files_sha256=c.sha(manifest))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--go',required=True,type=Path)
    parser.add_argument('--go-sha256',required=True)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    try:
        print(json.dumps(assemble(args.go,args.go_sha256,args.output_dir)))
    except Exception:
        print(json.dumps({'passed':False,'rule':'assembly_failed_preserve_output_no_retry'})); sys.exit(1)
