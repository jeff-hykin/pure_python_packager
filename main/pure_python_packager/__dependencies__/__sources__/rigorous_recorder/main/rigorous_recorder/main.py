from time import time as now
from random import random
import json

from .__dependencies__ import file_system_py as FS
from .__dependencies__.super_map import LazyDict
from .__dependencies__.super_hash import super_hash

# TODO:
    # have each experiment be given their own pickle file

# 
# helpers
# 
def large_pickle_load(file_path):
    """
    This is for loading really big python objects from pickle files
    ~4Gb max value
    """
    import pickle
    import os
    max_bytes = 2**31 - 1
    bytes_in = bytearray(0)
    input_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f_in:
        for _ in range(0, input_size, max_bytes):
            bytes_in += f_in.read(max_bytes)
    output = pickle.loads(bytes_in)
    return output

def large_pickle_save(variable, file_path):
    """
    This is for saving really big python objects into a file
    so that they can be loaded in later
    ~4Gb max value
    """
    import pickle
    bytes_out = pickle.dumps(variable, protocol=4)
    max_bytes = 2**31 - 1
    FS.clear_a_path_for(file_path, overwrite=True)
    with open(file_path, 'wb') as f_out:
        for idx in range(0, len(bytes_out), max_bytes):
            f_out.write(bytes_out[idx:idx+max_bytes])

# save loading times without brittle code
def attempt(a_lambda, default=None, expected_errors=(Exception,)):
    try:
        return a_lambda()
    except expected_errors:
        return default

def indent(string):
    return string.replace("\n", "\n    ")

# 
# 
# Main code
# 
# 
class AncestorDict(dict):
    def __init__(self, *, ancestors, itself=None):
        self.ancestors = ancestors
        if not isinstance(self.ancestors, (list, tuple)):
            raise Exception('for AncestorDict(), ancestors needs to be a dict')
        if itself != None and type(itself) != dict:
            raise Exception('for AncestorDict(), itself needs to be a pure dict')
        self.itself = itself or {}
    
    @property
    def lineage(self):
        yield self.itself
        for each in self.ancestors:
            yield each
    
    def keys(self):
        self_keys = self.itself.keys()
        for each_key in self_keys:
            yield each_key
        self_keys = set(self_keys)
        for each_parent in self.ancestors:
            for each_key in each_parent.keys():
                if each_key not in self_keys:
                    self_keys.add(each_key)
                    yield each_key
    
    def values(self):
        self_keys = self.itself.keys()
        for each_key, each_value in self.itself.items():
            yield each_value
        self_keys = set(self_keys)
        for each_parent in self.ancestors:
            for each_key, each_value in each_parent.items():
                if each_key not in self_keys:
                    self_keys.add(each_key)
                    yield each_value
    
    def items(self):
        self_keys = self.itself.keys()
        for each_key, each_value in self.itself.items():
            yield (each_key, each_value)
        self_keys = set(self_keys)
        for each_parent in self.ancestors:
            for each_key, each_value in each_parent.items():
                if each_key not in self_keys:
                    self_keys.add(each_key)
                    yield (each_key, each_value)
    
    def __len__(self):
        return len(tuple(self.keys()))
    
    def __iter__(self):
        return (each for each in self.keys())
    
    def __contains__(self, key):
        return any((key in each_person.keys() for each_person in self.lineage))
        
    def __getitem__(self, key):
        for each_person in self.lineage:
            if key in each_person.keys():
                return each_person[key]
        return None
    
    def __setitem__(self, key, value):
        # this happens because of pickling
        if not hasattr(self, "itself"):
            self.itself = {}
        self.itself[key] = value

    def update(self, other):
        self.itself.update(other)
    
    @property
    def compressed(self):
        copy = {}
        for each in reversed(tuple(self.lineage)):
            copy.update(each)
        return copy
    
    def __repr__(self,):
        copy = LazyDict(self.compressed)
        return copy.__repr__()
    
    def get(self,*args,**kwargs):
        return self.compressed.get(*args,**kwargs)
    
    def copy(self,*args,**kwargs):
        return self.compressed.copy(*args,**kwargs)

    def clone(self):
        return AncestorDict(
            ancestors=self.ancestors,
            itself=dict(self.itself),
        )
    
    def __getstate__(self):
        return self.itself, self.ancestors
    
    def __setstate__(self, state):
        self.itself, self.ancestors = state
    
    def __json__(self):
        return self.compressed

    def __deep_copy__(self, memo={}):
        from copy import deepcopy
        if id(self) in memo:
            return memo[id(self)]
        
        new_itself = {}
        the_copy = AncestorDict(
            ancestors=list(self.ancestors),
            itself=new_itself,
        )
        memo[id(self)] = the_copy
        # cant call deepcopy until id(self) is added to the memo
        for each_key, each_value in self.itself.items():
            new_itself[each_key] = deepcopy(each_value, memo)
        
        return the_copy

class AncestorMask(dict):
    def __init__(self, *, ancestors, index, frame):
        self.ancestors = ancestors
        if not isinstance(self.ancestors, (list, tuple)):
            raise Exception('for AncestorDict(), ancestors needs to be a list or tuple')
        if type(frame) != dict:
            raise Exception('for AncestorDict(), frame needs to be a pure dict')
        self.frame = frame
        self.index = index
    
    @property
    def itself(self):
        value = {}
        frame = self.frame
        index = self.index
        for each_key, each_value in frame.items():
            value[each_key] = frame[each_key][index]
        return value
    
    @property
    def lineage(self):
        yield self.itself
        for each in self.ancestors:
            yield each
    
    def keys(self):
        self_keys = self.frame.keys()
        for each_key in self_keys:
            if each_key is not None:
                yield each_key
        self_keys = set(self_keys)
        for each_parent in self.ancestors:
            for each_key in each_parent.keys():
                if each_key not in self_keys:
                    self_keys.add(each_key)
                    yield each_key
    
    def values(self):
        self_keys = self.frame.keys()
        for each_key, each_value in self.itself.items():
            if each_key is not None:
                yield each_value
        self_keys = set(self_keys)
        for each_parent in self.ancestors:
            for each_key, each_value in each_parent.items():
                if each_key not in self_keys:
                    self_keys.add(each_key)
                    yield each_value
    
    def items(self):
        self_keys = self.frame.keys()
        for each_key, each_value in self.itself.items():
            if each_key is not None:
                yield (each_key, each_value)
        self_keys = set(self_keys)
        for each_parent in self.ancestors:
            for each_key, each_value in each_parent.items():
                if each_key not in self_keys:
                    self_keys.add(each_key)
                    yield (each_key, each_value)
    
    def __len__(self):
        return len(tuple(self.keys()))
    
    def __iter__(self):
        return (each for each in self.keys())
    
    def __contains__(self, key):
        return any((key in each_person.keys() for each_person in self.lineage))
        
    def __getitem__(self, key):
        for each_person in self.lineage:
            if key in each_person.keys():
                return each_person[key]
        return None
    
    def __setitem__(self, key, value):
        # if adding a new key
        if key not in self.frame:
            first_key = next(self.frame.keys().__iter__())
            number_of_records = len(self.frame[first_key])
            self.frame[key] = [None]*number_of_records
        
        self.frame[key][self.index] = value

    def update(self, other):
        # use the __setitem__ over and over again
        for each_key, each_value in other.items():
            self[each_key] = each_value
    
    @property
    def compressed(self):
        copy = {}
        for each in reversed(tuple(self.lineage)):
            copy.update(each)
        if None in copy:
            del copy[None]
        return copy
    
    def __repr__(self,):
        copy = LazyDict(self.compressed)
        return copy.__repr__()
    
    def get(self,*args,**kwargs):
        return self.compressed.get(*args,**kwargs)
    
    def copy(self,*args,**kwargs):
        return self.compressed.copy(*args,**kwargs)

    def clone(self):
        return AncestorDict(
            ancestors=self.ancestors,
            itself=dict(self.itself),
        )
    
    def __getstate__(self):
        return self.index, self.frame, self.ancestors
    
    def __setstate__(self, state):
        self.index, self.frame, self.ancestors = state
    
    def __json__(self):
        return self.compressed
        
    def __deep_copy__(self, memo={}):
        from copy import deepcopy
        self_id = id(self)
        if self_id in memo:
            return memo[self_id]
        
        new_frame = {}
        the_copy = AncestorMask(
            ancestors=list(self.ancestors),
            index=self.index,
            frame=new_frame,
        )
        memo[self_id] = the_copy
        # cant call deepcopy until id(self) is added to the memo
        for each_key, each_value in self.frame.items():
            new_frame[each_key] = deepcopy(each_value, memo)
        
        return the_copy

class Recorder():
    @classmethod
    def load_from(self, path):
        return large_pickle_load(path)
    
    def __init__(self, data=None, **kwargs):
        """
        Examples:
            RecordKeeper()
            RecordKeeper({"key_of_data": "value"})
            RecordKeeper(key_of_data="value)
            RecordKeeper({}, parent_record_keeper)
        """
        # properties (each are updated below)
        self.local_data     = LazyDict(data or {}).merge(kwargs)
        self.sub_recorders  = []
        self.length         = 0
        self.frame          = {}
        self.parent         = None
        self.pending_record = {None:None}
    
    def set_parent(self, parent):
        self.parent = parent
        # attach self to parent
        self.parent.sub_recorders.append(self)
        return self
    
    def local_data_lineage_generator(self):
        yield self.local_data
        next_recorder = self
        while isinstance(next_recorder.parent, RecordKeeper):
            yield next_recorder.parent.local_data
            next_recorder = next_recorder.parent
    
    @property
    def local_data_lineage(self):
        return tuple(self.local_data_lineage_generator())
    
    @property
    def records(self):
        for index in range(self.length):
            yield AncestorMask(ancestors=self.local_data_lineage, index=index, frame=self.frame)
    
    @property
    def all_records(self):
        for each in self.records:
            yield each
        for each_sub_recorder in self.sub_recorders:
            for each_record in each_sub_recorder.all_records:
                yield each_record
    
    @property
    def full(self):
        if len(self.sub_recorders) == 0:
            return self
        
        full_value = Recorder()
        full_value.local_data     = self.local_data
        full_value.parent         = self.parent
        
        # get all keys (recursive)
        new_frame = { each_key: [] for each_key in self.keys() }
        for each_sub_record_keeper in self.sub_recorders:
            for each_key in each_sub_record_keeper.keys():
                new_frame[each_key] = []
            for each_key in each_sub_record_keeper.frame.keys():
                new_frame[each_key] = []
            for each_key in each_sub_record_keeper.full.frame.keys():
                new_frame[each_key] = []
        
        # get all frames (recursive)
        mock_self = LazyDict(full=self)
        for each_sub_record_keeper in (mock_self, *self.sub_recorders):
            length = each_sub_record_keeper.full.length
            full_value.length += length
            sub_frame = each_sub_record_keeper.full.frame
            for each_key in new_frame.keys():
                if each_key not in sub_frame:
                    sub_frame[each_key] = [self.get(each_key, each_sub_record_keeper.get(each_key, None))]*length
                # append all the new values
                new_frame[each_key] += sub_frame[each_key]
        full_value.frame = new_frame
        return full_value
    
    def push(self, data=None, **kwargs):
        self.length += 1
        pending_record = self.pending_record
        pending_record.update(data or {})
        pending_record.update(kwargs)
        
        frame = self.frame
        # extend everything down by 1
        for each_key, each_value in self.frame.items():
            each_value.append(None)
        # add the real new values
        for each_key, each_value in pending_record.items():
            if each_key not in frame:
                frame[each_key] = [None]*self.length
                frame[each_key][-1] = each_value
            else:
                frame[each_key][self.length-1] = each_value
            
        self.pending_record = {None:None}
        return self

    def add(self, data=None, **kwargs):
        self.pending_record.update(data or {})
        self.pending_record.update(kwargs)
        return self

    def commit(self):
        return self.push()
    
    def swap_out(self, old_record_keeper, new_record_keeper):
        next_keeper = self
        while isinstance(next_keeper.parent, RecordKeeper):
            if id(next_keeper.parent) == id(old_record_keeper):
                next_keeper.parent = new_record_keeper
                return True
            # TODO: add infinte loop check (like if next_keeper.parent == next_keeper) 
            next_keeper = next_keeper.parent
    
    def SubRecorder(self, **kwargs):
        return Recorder(kwargs).set_parent(self)
    
    def __iter__(self):
        return self.records
    
    def __len__(self):
        return self.length
    
    def __hash__(self):
        return super_hash({ Recorder: self.local_data })
        
    def __repr__(self):
        size = len(self)
        # fallback case first
        representer = attempt(lambda: indent(representer.__repr__()), default=self.local_data)
        # ideal case
        representer = attempt(lambda: indent(json.dumps(self.local_data, indent=4)), default=representer)
        # parent data
        all_parents = []
        parent_data = "    {"
        if self.parent:
            for each_key, each_value in self.parent.items():
                parent_data += f'\n        "{each_key}":' + indent(
                    attempt(lambda: json.dumps(each_value, indent=4), default=f"{each_value}")
                )
        parent_data += "\n    }"
        
        return f"""{'{'}\n    number_of_records: {size},\n    records: [ ... ],\n    local_data: {representer},\n    parent_data:{parent_data}\n{'}'}"""
    
    def __getitem__(self, key):
        # numerical acts like array of local records 
        if isinstance(key, int):
            return AncestorMask(ancestors=self.local_data_lineage, index=key, frame=self.frame)
        elif isinstance(key, slice):
            length = self.length
            start = key.start or 0
            stop = key.stop or length
            step = key.step or 1
            # negative indices
            start = start if start > 0 else length - start
            stop  = stop  if stop  > 0 else length - stop
            
            return tuple(
                AncestorMask(ancestors=self.local_data_lineage, index=key, frame=self.frame)
                    for index in range(start, stop, step)
            )
        # all else acts like dict of local data
        else:
            return self.local_data[key]
    
    def __setitem__(self, key, value):
        # numerical acts like array of local records 
        if isinstance(key, (int, slice)):
            self.local_records[key] = value
        # all else acts like dict of local data
        else:
            self.local_data[key] = value
    
    def get(self, key, default=None):
        # numerical acts like array of local records 
        if isinstance(key, (int, slice)):
            try:
                return self.local_records[key]
            except Exception as error:
                return default
        # all else acts like dict of local data
        else:
            if key in self.local_data:
                return self.local_data[key]
            else:
                return default
    
    def items(self, *args, **kwargs):
        return self.local_data.items(*args, **kwargs)
    
    def keys(self, *args, **kwargs):
        return self.local_data.keys(*args, **kwargs)
    
    def values(self, *args, **kwargs):
        return self.local_data.values(*args, **kwargs)
    
    def __getstate__(self):
        return (self.parent, self.local_data, self.sub_recorders, self.pending_record, self.frame, self.length)
    
    def __setstate__(self, state):
        self.parent, self.local_data, self.sub_recorders, self.pending_record, self.frame, self.length = state
        self._collection = None

    def save_to(self, path):
        large_pickle_save(self, path)

class RecordKeeper():
    @classmethod
    def load_from(self, path):
        return large_pickle_load(path)
    
    def __init__(self, *args, **kwargs):
        """
        Examples:
            RecordKeeper()
            RecordKeeper({"key_of_data": "value"})
            RecordKeeper(key_of_data="value)
            RecordKeeper({}, parent_record_keeper)
        """
        # properties (each are updated below)
        self.local_data         = LazyDict()
        self.sub_record_keepers = []
        self.local_records      = []
        self.parent             = None
        self.pending_record     = AncestorDict(ancestors=tuple()) 
        self.collection_id      = None
        self._collection        = None
        self._live_files        = []
        
        # load local data
        if len(args) == 1:
            first_arg = args[0]
            if isinstance(first_arg, dict):
                self.local_data = LazyDict(first_arg)
            else:
                raise Exception(f'''\n\ncalled RecordKeeper(data)\nbut data was: {first_arg}\nwhich was not a dict (and this object only works if it is)\n''')
        
        self.local_data.update(kwargs)
        
    def set_parent(self, parent):
        self.parent = parent
        self.pending_record = AncestorDict(ancestors=self.local_data_lineage, itself=dict(self.pending_record.itself))
        self.collection_id = self.parent.collection_id
        # attach self to parent
        self.parent.sub_record_keepers.append(self)
        
        return self
    
    def local_data_lineage_generator(self):
        yield self.local_data
        next_keeper = self
        while isinstance(next_keeper.parent, RecordKeeper):
            yield next_keeper.parent.local_data
            next_keeper = next_keeper.parent
    
    @property
    def collection(self):
        if self._collection:
            return self._collection
        
        if self.collection_id is not None:
            # collection corrisponding to the file path, if it exists
            # this is global var because of python pickling
            # this re-attaches self.collection to the collection (which avoids pickling/unpickling the whole collection)
            self._collection = globals().get("_ExperimentCollection_register",{}).get(self.collection_id, None)
            
            # TODO: if self._collection is still None, this should probably issue a warning
        
        return self._collection
    
    @property
    def local_data_lineage(self):
        return tuple(self.local_data_lineage_generator())
    
    @property
    def records(self):
        if self.collection is None:
            return self.local_records
        else:
            # look through all the records, even if they weren't generated in this runtime/session
            def generator():
                for each_record in self.collection.records:
                    # if this record was apart of a record, then report it
                    if self.local_data in each_record.ancestors:
                        yield each_record
            return generator()
    
    @property
    def all_records(self):
        for each in self.local_records:
            yield each
        for each_sub_record_keeper in self.sub_record_keepers:
            for each_record in each_sub_record_keeper.all_records:
                yield each_record
    
    def push(self, data=None, **kwargs):
        data = {} if data is None else data
        data.update(kwargs)
        self.commit(additional_info=data)
        return self

    def add(self, *args, **kwargs):
        data = {}
        if len(args) > 0:
            data = args[0]
        data.update(kwargs)
        self.pending_record.update(data)
        return self

    def commit(self,*, additional_info=None):
        # finalize the record
        if isinstance(additional_info, dict): 
            self.pending_record.update(additional_info)
        # make sure the ancestors are the most up-to-date (swap_out can cause them to change since init)
        local_lineage = self.local_data_lineage
        self.pending_record.ancestors = local_lineage
        # save different depending on if part of a collection or not
        output = self.pending_record
        if self.collection is not None:
            self.collection.add_record(self.pending_record)
        else:
            self.local_records.append(self.pending_record)
        
        for each in self._live_files:
            each.write("- "+json.dumps(self.pending_record.itself)+"\n")
            each.flush()
        
        # start a new clean record
        self.pending_record = AncestorDict(ancestors=local_lineage)
        # return the record (AncestorDict) that was just committed
        return output
    
    def swap_out(self, old_record_keeper, new_record_keeper):
        next_keeper = self
        while isinstance(next_keeper.parent, RecordKeeper):
            if id(next_keeper.parent) == id(old_record_keeper):
                next_keeper.parent = new_record_keeper
                return True
            # TODO: add infinte loop check (like if next_keeper.parent == next_keeper) 
            next_keeper = next_keeper.parent
    
    @property
    def number_of_records(self):
        return len(self)
    
    def SubRecordKeeper(self, **kwargs):
        return RecordKeeper(kwargs).set_parent(self)
    
    def __iter__(self):
        for each in self.records:
            yield each
    
    def __len__(self):
        if self.collection is None:
            return len(self.local_records)
        else:
            # apparently this is the fastest way (no idea why converting to tuple is faster than using reduce)
            return len(tuple(self.records))
    
    def __hash__(self):
        return super_hash({ RecordKeeper: self.local_data })
        
    def __repr__(self):
        size = len(self)
        # fallback case first
        representer = attempt(lambda: indent(representer.__repr__()), default=self.local_data)
        # ideal case
        representer = attempt(lambda: indent(json.dumps(self.local_data, indent=4)), default=representer)
        # parent data
        all_parents = []
        parent_data = "    {"
        if self.parent:
            for each_key, each_value in self.parent.items():
                parent_data += f'\n        "{each_key}":' + indent(
                    attempt(lambda: json.dumps(each_value, indent=4), default=f"{each_value}")
                )
        parent_data += "\n    }"
        
        return f"""{'{'}\n    number_of_records: {size},\n    records: [ ... ],\n    local_data: {representer},\n    parent_data:{parent_data}\n{'}'}"""
    
    def __getitem__(self, key):
        # numerical acts like array of local records 
        if isinstance(key, (int, slice)):
            return self.local_records[key]
        # all else acts like dict of local data
        else:
            return self.local_data[key]
    
    def __setitem__(self, key, value):
        # numerical acts like array of local records 
        if isinstance(key, (int, slice)):
            self.local_records[key] = value
        # all else acts like dict of local data
        else:
            self.local_data[key] = value
    
    def get(self, key, default=None):
        # numerical acts like array of local records 
        if isinstance(key, (int, slice)):
            try:
                return self.local_records[key]
            except Exception as error:
                return default
        # all else acts like dict of local data
        else:
            if key in self.local_data:
                return self.local_data[key]
            else:
                return default
    
    def items(self, *args, **kwargs):
        return self.local_data.items(*args, **kwargs)
    
    def keys(self, *args, **kwargs):
        return self.local_data.keys(*args, **kwargs)
    
    def values(self, *args, **kwargs):
        return self.local_data.values(*args, **kwargs)
    
    def __getstate__(self):
        return (self.parent, self.local_data, self.collection_id, self.sub_record_keepers, self.pending_record, self.local_records)
    
    def __setstate__(self, state):
        self.parent, self.local_data, self.collection_id, self.sub_record_keepers, self.pending_record, self.local_records = state

    def save_to(self, path):
        large_pickle_save(self, path)
    
    def __json__(self):
        return [ each.__json__() for each in self ]
    
    def live_write_to(self, path, *, as_yaml=None):
        if as_yaml != True:
            raise Exception(f'''.live_write_to() currently needs the argument as_yaml=True\ne.g. .live_write_to(path, as_yaml=True)''')
        
        # clear existing data, make sure folder exists
        FS.write(data="", to=path)
        local_and_parent_data = AncestorDict(ancestors=self.local_data_lineage).__json__()
        self._live_files.append(open(path, 'a'))
        self._live_files[-1].write(f'''parent_data_snapshot: {json.dumps(local_and_parent_data, indent=4)}\n''')
        self._live_files[-1].write(f'''records:\n''')
    
    def __del__(self):
        for each in self._live_files:
            each.close()

class Experiment(object):
    def __init__(self, internal_experiment_info, save_experiment):
        self.current_experiment = internal_experiment_info
        self.save_experiment    = save_experiment
    
    def __enter__(self):
        return self.current_experiment
    
    def __exit__(self, _, error, traceback):
        self.save_experiment(_, error, traceback)

class ExperimentCollection:
    """
    Example:
        collection = ExperimentCollection("test1") # filepath 
        with collection.new_experiment() as record_keeper:
            pass
    Note:
        the top most record keeper will be automatically be given these values:
        (all of these can be overridden)
        - experiment_number
        - error_number
        - had_error
        - experiment_start_time
        - experiment_end_time
        - experiment_duration
    """
    
    # TODO: make it so that Experiments uses database with detached/reattached pickled objects instead of a single pickle file
    
    def __init__(self, folder_path, quiet=False, records=None, extension=".collection"):
        self.folder_path                         = FS.make_absolute_path(folder_path+extension)
        self.quiet                               = quiet
        self.id                                  = None # will be changed almost immediately
        self.collection_name                     = FS.name(self.folder_path)
        self._records                            = None
        self._new_records                        = records or []
        self.collection_keeper                   = RecordKeeper({})
        self.internal_experiment_info            = None
        self.current_experiment                  = None
        self.prev_internal_experiment_local_data = dict(experiment_number=0, error_number=0, had_error=False)
        
        self.sub_paths = LazyDict(
            id=f"{self.folder_path}/collection_id.txt",
            collection_info=f"{self.folder_path}/collection_info.pickle",
            records=f"{self.folder_path}/records.pickle",
        )
        
        # create the main folder if it doesn't exist
        FS.ensure_is_folder(self.folder_path)
        
        # 
        # load/set self.id
        # 
        if FS.is_file(self.sub_paths.id):
            self.id = FS.read(self.sub_paths.id)
        else:
            if not self.quiet: print(f'Will create new experiment collection: {self.collection_name}')
            self.id = f"{random()}"
            FS.write(data=self.id, to=self.sub_paths.id)
        # when a record_keeper is saved, it shouldn't contain a copy of the experiment collection
        # (otherwise every record keeper would contain the entire collection instead of being Independent)
        # however, when record_keeper loads itself back, it should reconnect to the experiment_collection if its available
        # and thats exactly what this method here is doing
        # TODO: look into the "dill" package as a possible alternative
        register = globals()["_ExperimentCollection_register"] = globals().get("_ExperimentCollection_register", {})
        register[self.id] = self
        
        # attach the root RecordKeeper to the collection (makes the RecordKeeper kind of special)
        self.collection_keeper.collection_id = self.id
        
        self.load_basic_info()
    
    def load_basic_info(self):
        self.prev_internal_experiment_local_data = self.prev_internal_experiment_local_data or dict(experiment_number=0, error_number=0, had_error=False)
        if FS.is_file(self.sub_paths.collection_info):
            self.collection_keeper.local_data, self.prev_internal_experiment_local_data = large_pickle_load(self.sub_paths.collection_info)
        
    def load_records(self):
        if FS.is_file(self.sub_paths.records):
            self._records = large_pickle_load(self.sub_paths.records) or []
        else:
            self._records = []
    
    def reload(self):
        self.load_basic_info()
        self._records = None # records will do an on-demand reload because it can be a really slow operation
        
    @property
    def records(self):
        if self._records is None:
            self.load_records()
        return self._records + self._new_records
    
    def __len__(self,):
        return len(self.records)
    
    def add_record(self, record):
        self._new_records.append(record)
    
    @property
    def experiment_numbers(self):
        experiment_numbers = set()
        # must manually calculate because experiments can be deleted
        for each in self.records:
            experiment_numbers.add(each.get("experiment_number", None))
        return tuple(experiment_numbers)
        
    def __getitem__(self, key):
        experiment_numbers = self.experiment_numbers
        if key < 0:
            key = experiment_numbers[key]
        if key not in experiment_numbers:
            return []
        return tuple(each for each in self.records if each.get("experiment_number",None) == key)
    
    def save(self):
        relative_path = FS.make_relative_path(to=self.folder_path)
        if not self.quiet: print(f"Saving experiment: {self.internal_experiment_info.local_data}")
        FS.ensure_is_folder(self.folder_path)
        # save basic collection info
        large_pickle_save((self.collection_keeper.local_data, self.internal_experiment_info.local_data), self.sub_paths.collection_info)
        records = self.records
        if not self.quiet: print(f"Saving {len(records)} records")
        # save records
        large_pickle_save(records, self.sub_paths.records)
        self._records = records
        self._new_records.clear() # remove out new records whenever they're saved to prevent .reload() from adding duplicates
        if not self.quiet: print(f"Experiment collection saved in: {relative_path}")
    
    def new_experiment(self, experiment_info=None, **kwargs):
        experiment_info = experiment_info if experiment_info else {}
        experiment_info.update(kwargs)
        # add basic data to the experiment
        # there are 3 levels:
        # - self.collection_keeper.local_data (root) => data about the collection
        # - self.internal_experiment_info            => automated data about the experiment
        # - self.current_experiment                  => user-data about the experiment
        self.internal_experiment_info = RecordKeeper(
            experiment_number=self.prev_internal_experiment_local_data["experiment_number"] + 1 if not self.prev_internal_experiment_local_data["had_error"] else self.prev_internal_experiment_local_data["experiment_number"],
            error_number=self.prev_internal_experiment_local_data["error_number"]+1,
            had_error=True, # default assumption => is later set to False (if it succeeds)
            experiment_start_time=now(),
        ).set_parent(self.collection_keeper)
        
        self.current_experiment = RecordKeeper(experiment_info).set_parent(self.internal_experiment_info)
        
        def save_experiment(_, error, traceback):
            # mutate the internal experiment record keeper based on having an error or not
            no_error = error is None
            experiment_info = self.internal_experiment_info.local_data
            experiment_info["experiment_end_time"] = now()
            experiment_info["experiment_duration"] = experiment_info["experiment_end_time"] - experiment_info["experiment_start_time"]
            if no_error:
                experiment_info["had_error"] = False
                experiment_info["error_number"] = 0
            
            # save to storage
            self.save()
            
            # "this" experiment has now become "previous" experiment
            self.prev_internal_experiment_local_data = self.internal_experiment_info.local_data
            
            # re-throw if error occured
            if not no_error:
                print(f'There was an error when running an experiment. Experiment collection: "{self.collection_name}"')
                print(f'However, the partial experiment data was saved')
                experiment_number = self.internal_experiment_info.local_data["experiment_number"]
                error_number = self.internal_experiment_info.local_data["error_number"]
                import traceback
                print(f'This happend on:\n    dict(experiment_number={experiment_number}, error_number={error_number})')
                print(traceback.format_exc())
                raise error
        
        return Experiment(
            internal_experiment_info=self.current_experiment,
            save_experiment=save_experiment,
        )
    
    
    
    
