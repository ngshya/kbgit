from abc import ABC, abstractmethod


class DatabaseConnection(ABC):

    '''KBD'''

    @abstractmethod
    def kbd_exists_collection(self):
        pass

    @abstractmethod
    def kbd_create_collection(self):
        pass

    def kbd_create_collection_if_not_exists(self):
        if not self.kbd_exists_collection():
            self.kbd_create_collection()

    def kbd_exists(self, kbd_id):
        return len(self.kbd_search_by_id(kbd_id=kbd_id)) > 0

    @abstractmethod
    def kbd_update(self, kbd):
        pass

    @abstractmethod
    def kbd_search_by_id(self, kbd_id):
        pass

    '''KBN'''

    @abstractmethod
    def kbn_exists_collection(self):
        pass

    @abstractmethod
    def kbn_create_collection(self):
        pass

    def kbn_create_collection_if_not_exists(self):
        if not self.kbn_exists_collection():
            self.kbn_create_collection()

    def kbn_exists(self, kbn_id):
        return len(self.kbn_search_by_id(kbn_id=kbn_id)) > 0

    @abstractmethod
    def kbn_create(self, kbn_id, kbb_id, kbb_tms):
        pass

    @abstractmethod
    def kbn_search_by_id(self, kbn_id):
        pass

    @abstractmethod
    def kbn_add_new_kbb(self, kbn_id, kbb_id, kbb_tms):
        pass

    @abstractmethod
    def kbn_get_last_kbb_id(self, kbn_id):
        pass

    ''' KBB '''

    @abstractmethod
    def kbb_exists_collection(self):
        pass

    @abstractmethod
    def kbb_create_collection(self):
        pass

    def kbb_create_collection_if_not_exists(self):
        if not self.kbb_exists_collection():
            self.kbb_create_collection()

    def kbb_exists(self, kbb_id):
        return len(self.kbb_search_by_id(kbb_id=kbb_id)) > 0

    @abstractmethod
    def kbb_create(self, kbb):
        pass

    @abstractmethod
    def kbb_search_by_id(self, kbb_id):
        pass

    @abstractmethod
    def kbb_search_by_text(
        self, 
        text, 
        kbb_ids_to_query=[], 
        distance=1.0, 
        n_results=3
    ):
        pass
