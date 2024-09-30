from uuid import uuid4
from time import time
from typing import Dict, List, Union, Any, Self
from ..db.tools import get_db_connection
from .block import KBB


class KBD:
    """
    KBD class represents a Knowledge Base Document.

    This class encapsulates a collection of knowledge base blocks (KBB),
    allowing the user to perform operations such as adding, removing, and
    searching for KBB entries. It manages the relationships between KBB entries
    and can retrieve information from the Document.
    """

    def __init__(self, kbbs: List[KBB] = [], kbd_id: Union[str, None] = None):
        """
        Initialize a KBD instance.

        This constructor sets up the KBD object based on the provided 
        parameters. It either pulls data from the database if a KBD ID is 
        provided, or initializes a new KBD entry if KBBs are provided.

        Args:
            kbbs (List[KBB], optional): A list of KBB objects associated with 
                this KBD.
            kbd_id (Union[str, None], optional): The ID of an existing KBD to 
                initialize from.
        """
        self.data: Dict[str, Any] = {}
        if len(kbbs) > 0:
            self.data["kbd_id"] = f"kbd_{uuid4()}"
            self.data["kbbs"] = kbbs
            self.data["kbb_ids"] = [_.data["kbb_id"] for _ in kbbs]
            self.data["operations"] = [
                {
                    "operation": "create", 
                    "kbbs_snapshot": [_.data["kbb_id"] for _ in kbbs], 
                    "tms": time()
                }
            ]
            self.data["state"] = "uncomputed"
        elif kbd_id is not None:
            db_connection = get_db_connection()
            self.data = db_connection.kbd_search_by_id(self, kbd_id)
            self.data["kbbs"] = [KBB(kbb_id=_) for _ in self.data["kbb_ids"]]
        else:
            self.data["kbd_id"] = f"kbd_{uuid4()}"
            self.data["kbbs"] = []
            self.data["kbb_ids"] = []
            self.data["operations"] = [
                {
                    "operation": "create", 
                    "kbbs_snapshot": [], 
                    "tms": time()
                }
            ]
            self.data["state"] = "uncomputed"            

    def __add__(self, kbd: Self) -> "KBD": 
        """
        Combine two KBD entries into a new KBD entry.

        This method returns a new KBD entry containing all KBBs from both 
        KBD instances, while ensuring that no duplicate KBBs are included.

        Args:
            kbd (KBD): Another KBD instance to add.

        Returns:
            KBD: A new KBD instance that combines the KBBs of both instances.
        """
        new_kbd = KBD(
            kbbs = self.data["kbbs"] + \
                [_ for _ in kbd.data["kbbs"] \
                 if _.data["kbb_id"] not in self.data["kbb_ids"]]
        )
        new_kbd.data["operations"][0]["operation"] = "sum"
        list_parents: List[str] = []
        if (self.data["state"] == "uncomputed") and (self.data["operations"][-1]["operation"] == "sum"):
            list_parents = list_parents + self.data["operations"][-1]["parents_kbd"]
        else:
            list_parents.append(self.data["kbd_id"])
        if (kbd.data["state"] == "uncomputed") and (kbd.data["operations"][-1]["operation"] == "sum"):
            list_parents = list_parents + kbd.data["operations"][-1]["parents_kbd"]
        else:
            list_parents.append(kbd.data["kbd_id"])
        new_kbd.data["operations"][0]["parents_kbd"] = list_parents
        return new_kbd
    
    def __radd__(self, kbd: Self) -> "KBD":
        """
        Enable right-hand addition of KBD entries.
        """
        if kbd == 0:
            return self
        else:
            return self + kbd

    def __sub__(self, kbd: Self) -> "KBD":
        """
        Subtract a KBB entry from this KBD.

        This method creates a new KBD instance that excludes KBBs present
        in the provided KBD instance.

        Args:
            kbd (KBD): The KBD instance to subtract.

        Returns:
            KBD: A new KBD instance that contains KBBs from this instance
            excluding those in the given KBD.
        """
        new_kbbs = [_ for _ in self.data["kbbs"] if _.data["kbb_id"] not in kbd.data["kbb_ids"]]
        new_kbd = KBD(kbbs=new_kbbs)
        new_kbd.data["operations"][0]["operation"] = "sub"
        new_kbd.data["operations"][0]["parents_kbd"] = [self.data["kbd_id"], kbd.data["kbd_id"]]
        return new_kbd
        
    def __lt__(self, kbb: KBB):
        """
        Add a KBB entry to this KBD.

        This method adds a KBB entry to the KBD, updating metadata accordingly.

        Args:
            kbb (KBB): The KBB instance to add.
        """
        assert kbb.data["kbb_id"] not in self.data["kbb_ids"], \
            "KBB already in DOC."
        self.data["kbbs"].append(kbb)
        self.data["kbb_ids"].append(kbb.data["kbb_id"])
        self.data["operations"].append(
            {
                "operation": "add", 
                "kbb": [kbb.data["kbb_id"]], 
                "kbbs_snapshot": self.data["kbb_ids"].copy(), 
                "tms": time()
            }
        )
        self.data["state"] = "uncomputed"

    def __lshift__(self, kbb: KBB):
        """
        Add a KBB entry smartly using the left shift operator.

        This method checks if a KBB entry has similar KBB data from the KBD 
        and update the corresponding KBB already contained in the KBD.

        Args:
            kbb (KBB): The KBB instance to add.
        """
        assert kbb.data["kbb_id"] not in self.data["kbb_ids"], \
            "KBB already in DOC."
        for _ in self.data["kbbs"]:
            if _.data["state"] != "computed":
                _.compute()
        db_connection = get_db_connection()
        list_similar_kbb_data = db_connection.kbb_search_by_text(
            text=kbb.data["content"], 
            kbb_ids_to_query=self.data["kbb_ids"], 
            distance=1.0, 
            n_results=1
        )
        new_kbb = kbb
        if len(list_similar_kbb_data) > 0:
            similar_kbb = KBB(kbb_data=list_similar_kbb_data[0][1])
            new_kbb = similar_kbb + kbb
            self.data["kbbs"] = [_ for _ in self.data["kbbs"] if _.data["kbb_id"] != similar_kbb.data["kbb_id"]]
            self.data["kbb_ids"].remove(similar_kbb.data["kbb_id"])
        self.data["kbbs"].append(new_kbb)
        self.data["kbb_ids"].append(new_kbb.data["kbb_id"])
        self.data["operations"].append(
            {
                "operation": "smart add", 
                "kbb": [new_kbb.data["kbb_id"]], 
                "kbbs_snapshot": self.data["kbb_ids"].copy(), 
                "tms": time()
            }
        )
        self.data["state"] = "uncomputed"

    def __str__(self) -> str:
        """
        Return a string representation of the KBD.

        This method constructs a string that displays all KBB entries in the 
        KBD, showing their content and identifiers.

        Returns:
            str: A formatted string representing the contents of the KBD.
        """
        output = ""
        for kbb in self.data["kbbs"]:
            if kbb.data["state"] != "computed":
                kbb.compute()
            output = output + f"[{kbb.data['kbb_id']}] {kbb.data['content']} \n"
        return output

    def search_similar_kbb(
        self, 
        kbb: KBB, 
        distance: float = 1000, 
        n_results: int = 10
    ) -> List[Any]:
        """
        Search for similar KBB entries based on the content of a given KBB.

        This method compares the contents of the provided KBB against all KBBs
        in the KBD and retrieves similar entries.

        Args:
            kbb (KBB): The KBB instance to compare against.
            distance (float, optional): The maximum distance for matching KBBs. 
                Defaults to 1000.
            n_results (int, optional): The number of similar results to return. 
                Defaults to 10.

        Returns:
            List[Any]: A list of KBB entries that are similar to the given KBB.
        """
        if kbb.data["state"] != "computed":
            kbb.compute()
        if self.data["state"] != "computed":
            self.compute()
        db_connection = get_db_connection()
        list_similar_kbb_data = db_connection.kbb_serach_by_text(
            kbb.data["content"], 
            ids_to_query=self.data["kbb_ids"], 
            distance=distance, 
            n_results=n_results
        )
        return list_similar_kbb_data
        
    def compute(self):
        """
        Compute and finalize the state of the KBD.

        This method ensures that all KBB entries are computed and updates the 
        state of the KBD to 'computed'. It also updates the KBD in the database.
        """
        for kbb in self.data["kbbs"]:
            if kbb.data["state"] != "computed":
                kbb.compute()
        self.data["state"] = "computed"
        db_connection = get_db_connection()
        db_connection.kbd_update(self)

