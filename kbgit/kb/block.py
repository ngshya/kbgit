import os
from uuid import uuid4
from time import time
from datetime import datetime, timezone
from itertools import groupby
from igraph import Graph # type: ignore
from typing import Dict, List, Union, Any, Self
from ..db.tools import get_db_connection
from ..llm import get_embedding, llm_text_rewrite, llm_text_remove, llm_conflicts_detect, llm_correct
from ..log import logger

class KBB:
    """
    KBB class represents a knowledge block in a knowledge base.

    This class encapsulates the properties and behaviors of a knowledge base 
    block (KBB) in the database. It allows for the creation, updates, and 
    operations on KBB entries, and it handles interactions with the database to 
    retrieve KBB data.

    Attributes:
        data (dict): A dictionary storing attributes and their values related 
        to the KBB entry, including content, KBB ID, KBN ID, state, and 
        timestamps.
    """

    def __init__(
        self, 
        kbb_content: Union[str, None] = None,
        kbb_id: Union[str, None] = None,
        kbn_id: Union[str, None] = None,
        kbb_data: Union[None, Dict[str, Any]] = None,
    ):
        """
        Initialize a KBB instance.

        This constructor prepares a KBB object based on the provided parameters.
        It retrieves data from the database if a KBB ID is given or initializes 
        a new KBB entry using the provided content or data.

        Args:
            kbb_content (Union[str, None], optional): The content of the KBB. 
                Defaults to None.
            kbb_id (Union[str, None], optional): The ID of an existing KBB to 
                initialize from. Defaults to None.
            kbn_id (Union[str, None], optional): The ID of the associated KBN. 
                Defaults to None.
            kbb_data (Union[None, Dict[str, Any]], optional): A dictionary 
                containing comprehensive KBB data. Defaults to None.

        Raises:
            Exception: If no data is provided to initialize the KBB.
        """

        self.data = {}
        
        if kbb_id is not None:
            self._pull_from_db(kbb_id=kbb_id)
        elif kbb_data is not None:
            self.data = kbb_data
        elif kbb_content is not None:
            self.data = {"content": kbb_content}
        else:
            raise Exception("KBB initialization failed. No data provided")
        
        if "kbb_id" not in self.data.keys():
            self.data["kbb_id"] = f"kbb_{uuid4()}"
        if "kbn_id" not in self.data.keys():
            self.data["kbn_id"] = f"kbn_{uuid4()}"
        if "embedding" not in self.data.keys():
            EMBEDDING_OUTPUT_SIZE = os.getenv("EMBEDDING_OUTPUT_SIZE")
            if (EMBEDDING_OUTPUT_SIZE is None) or (EMBEDDING_OUTPUT_SIZE == ""):
                emb_output_size = 1
            else:
                emb_output_size = int(EMBEDDING_OUTPUT_SIZE)
            self.data["embedding"] = [0] * emb_output_size
        if "content" not in self.data.keys():
            self.data["content"] = ""
        if "parents_op" not in self.data.keys():
            self.data["parents_op"] = "create"
        if "parents_kbb" not in self.data.keys():
            self.data["parents_kbb"] = []
        if "state" not in self.data.keys():
            self.data["state"] = "uncomputed"
        if "tms_create" not in self.data.keys():
            self.data["tms_create"] = time()

        self.data["content"] = str(self.data["content"])


    def __str__(self) -> str:
        """
        Return a string representation of the KBB.

        This method generates a formatted string that displays the KBB's 
        content, IDs, and timestamps. If the KBB's state is not 'computed', 
        it computes the KBB before returning the string representation.

        Returns:
            str: A formatted string containing details about the KBB.
        """
        if self.data["state"] != "computed":
            self.compute(
                msg=f"Computed on {str(datetime.now(timezone.utc))} " + \
                    "to print the content."
            )
        output_string = \
            f'[{self.data["parents_op"]}] ' + \
            f'{self.data["content"]} ' + \
            f'[{self.data["kbb_id"]}] ' + \
            f'[{self.data["kbn_id"]}] ' + \
            f'[{datetime.fromtimestamp(float(self.data["tms_create"])).strftime("%Y-%m-%d %H:%M:%S")}] ' + \
            f'[{datetime.fromtimestamp(float(self.data["tms_compute"])).strftime("%Y-%m-%d %H:%M:%S")}] '
        return output_string


    def _pull_from_db(self, kbb_id: str):
        """
        Retrieve KBB data from the database.

        This private method fetches KBB data corresponding to the provided ID 
        and populates the KBB object's data attribute.

        Args:
            kbb_id (str): The ID of the KBB to be retrieved from the database.
        """
        db_connection = get_db_connection()
        kbb_data = db_connection.kbb_search_by_id(kbb_id)
        if len(kbb_data) > 0:
            self.data = kbb_data

    
    def edit_content(self, new_content: str) -> "KBB":
        """
        Edit the content of the KBB and return a new KBB object.

        This method creates a new KBB instance with updated content while 
        retaining the associated KBN ID.

        Args:
            new_content (str): The updated content for the KBB.

        Returns:
            KBB: A new KBB instance with the updated content.
        """
        if self.data["state"] != "computed":
            self.compute()
        return KBB(
            kbb_data={
                "content": new_content,
                "kbn_id": self.data["kbn_id"], 
                "parents_op": "edit",
                "parents_kbb": []
            }
        )


    def __sub__(self, kbb: Self) -> "KBB":
        """
        Create a new KBB instance representing a subtraction operation.

        This method defines how to subtract another KBB from this KBB, 
        generating a new KBB entry that records the operation.

        Args:
            kbb (Self): The KBB to subtract from this instance.

        Returns:
            KBB: A new KBB instance with details about the subtraction.
        """
        return KBB(
            kbb_data={
                "parents_op": "sub",
                "parents_kbb": [
                    {
                        "kbn_id": self.data["kbn_id"], 
                        "kbb_id": self.data["kbb_id"]
                    } \
                        if self.data["state"] == "computed" else self, 
                    {
                        "kbn_id": kbb.data["kbn_id"], 
                        "kbb_id": kbb.data["kbb_id"]
                    } \
                        if kbb.data["state"] == "computed" else kbb, 
                ]
            }
        )

    
    def __add__(self, kbb: Self) -> "KBB":
        """
        Combine two KBB entries into a new KBB entry.

        This method returns a new KBB entry containing information from both 
        KBB instances while ensuring that no conflicts are reported.

        Args:
            kbb (Self): Another KBB instance to add.

        Returns:
            KBB: A new KBB instance that combines the KBBs of both instances.
        """
        list_parents_kbb: List[Any] = []
        if (self.data["state"] == "computed"):
            list_parents_kbb.append(
                {
                    "kbn_id": self.data["kbn_id"], 
                    "kbb_id": self.data["kbb_id"]
                }
            )
        else:
            if self.data["parents_op"] == "sum":
                list_parents_kbb = list_parents_kbb + self.data["parents_kbb"]
            else: 
                list_parents_kbb.append(self)
        if (kbb.data["state"] == "computed"):
            list_parents_kbb.append(
                {
                    "kbn_id": kbb.data["kbn_id"], 
                    "kbb_id": kbb.data["kbb_id"]
                }
            )
        else:
            if kbb.data["parents_op"] == "sum":
                list_parents_kbb = list_parents_kbb + kbb.data["parents_kbb"]
            else: 
                list_parents_kbb.append(kbb)
        return KBB(
            kbb_data={
                "parents_op": "sum",
                "parents_kbb": list_parents_kbb
            }
        )


    def __radd__(self, kbb: Self) -> "KBB":
        """Enable right-hand addition of KBB entries."""
        if kbb == 0:
            return self
        else:
            return self + kbb  
    

    def compute(
        self, 
        msg: str = f"Computed on {str(datetime.now(timezone.utc))}.", 
    ):
        """
        Compute and finalize the state of the KBB.

        This method processes the KBB's data based on its current state and 
        relationships with parent KBB entries. It generates new content 
        based on the specified operation (creation, edit, sum, or subtraction) 
        and updates the KBB's state to 'computed'. The results are then saved 
        to the database.

        Args:
            msg (str, optional): An optional message to attach to the 
                computation log. Defaults to a timestamp indicating when the 
                computation was completed.

        Raises:
            AssertionError: If the KBB's state is not 'uncomputed' when this 
                method is called.
            AssertionError: If there is a mismatch between expected parent 
                operations and current state requirements.

        This method performs the following steps based on the `parents_op` 
            attribute:
            - If `parents_op` is "creation", it initializes the KBB without any 
                parents.
            - If `parents_op` is "edit", it requires there be no parents 
                already.
            - If `parents_op` is "sub", it expects exactly two parent KBBs.
            - If `parents_op` is "sum", it expects at least two parent KBBs.

        The method also updates the embedding for the KBB based on the newly 
            computed content, and logs the computation to the database.
        """
        assert (self.data["state"] == "uncomputed"), \
            "You can compute only uncomputed KBB."

        if self.data["parents_op"] in ["creation"]: 
            self.data["parents_kbb"] = []

        if self.data["parents_op"] in ["edit"]: 
            assert len(self.data["parents_kbb"]) == 0, \
                "The operation edit requires 1 parent."

        elif self.data["parents_op"] == "sub":
            assert len(self.data["parents_kbb"]) == 2, \
                "The operation sub requires two parents."
            list_parents_contents = []
            new_parents_kbb = []
            for parent_kbb in self.data["parents_kbb"]:
                if type(parent_kbb) == dict: # already computed
                    parent_kbb = KBB(kbb_id=parent_kbb["kbb_id"])
                else:
                    parent_kbb.compute(
                        msg=f"Computed on {str(datetime.now(timezone.utc))} "+\
                            f'because parent of {self.data["kbb_id"]}, '+\
                            f"operation sub."
                    )
                new_parents_kbb.append(
                    {
                        "kbn_id": parent_kbb.data["kbn_id"], 
                        "kbb_id": parent_kbb.data["kbb_id"]
                    }
                )
                if parent_kbb.data["parents_op"] in ["creation", "edit"]:
                    list_parents_contents.append(
                        llm_text_rewrite(text=parent_kbb.data["content"])["parsed_output"]
                    )
                else:
                    list_parents_contents.append(parent_kbb.data["content"])
            dict_content = llm_text_remove(
                text1=list_parents_contents[0],
                text2=list_parents_contents[1]
            )
            self.data["parents_kbb"] = new_parents_kbb
            self.data["content"] = dict_content["parsed_output"]
            self.data["content_raw"] = dict_content["raw_output"]

        elif self.data["parents_op"] == "sum":
            assert len(self.data["parents_kbb"]) >= 2, \
                "The operation sum requires more than one parent."
            list_parents_contents = []
            list_parents_tms_compute = []
            new_parents_kbb = []
            for parent_kbb in self.data["parents_kbb"]:
                if type(parent_kbb) == dict: # already computed
                    parent_kbb = KBB(kbb_id=parent_kbb["kbb_id"])
                else:
                    parent_kbb.compute(
                        msg=f"Computed on {str(datetime.now(timezone.utc))} "+\
                            f"because parent of {self.data['kbb_id']}, "+\
                            f"operation sum."
                    )
                new_parents_kbb.append(
                    {
                        "kbn_id": parent_kbb.data["kbn_id"], 
                        "kbb_id": parent_kbb.data["kbb_id"]
                    }
                )
                if parent_kbb.data["parents_op"] in ["creation", "edit"]:
                    list_parents_contents.append(
                        llm_text_rewrite(text=parent_kbb.data["content"])["parsed_output"]
                    )
                else:
                    list_parents_contents.append(parent_kbb.data["content"])
                list_parents_tms_compute.append(float(parent_kbb.data["tms_compute"]))
            list_parents_contents_ordered = [item for _, item in sorted(zip(list_parents_tms_compute, list_parents_contents))]
            dict_content = llm_text_rewrite(text=" \n".join(list_parents_contents_ordered))
            self.data["parents_kbb"] = new_parents_kbb
            self.data["content"] = dict_content["parsed_output"]
            self.data["content_raw"] = dict_content["raw_output"]

        self.data["embedding"] = get_embedding(self.data["content"])
        self.data["compute_msg"] = msg
        self.data["tms_compute"] = time()
        self.data["state"] = "computed"
        db_connection = get_db_connection()
        db_connection.kbb_create(self)

        if self.data["parents_op"] in ["create", "sum", "sub"]: 
            db_connection.kbn_create(
                kbn_id=self.data["kbn_id"], 
                kbb_id=self.data["kbb_id"], 
                kbb_tms=self.data["tms_compute"]
            )

        elif self.data["parents_op"] in ["edit"]: 
            db_connection.kbn_add_new_kbb(
                kbn_id=self.data["kbn_id"], 
                kbb_id=self.data["kbb_id"], 
                kbb_tms=self.data["tms_compute"]
            )


    def show_node_history(self):
        """
        Display the history of KBB nodes associated with this KBB.

        This method first checks if the KBB's state is 'computed'. If not, 
        it computes the KBB to ensure the history can be displayed.
        It then retrieves the relevant KBN entry from the database and 
        displays the history of KBBs that belong to this KBN.
        """
        if self.data["state"] != "computed":
            self.compute(
                msg=f"Computed on {str(datetime.now(timezone.utc))} " + \
                    "to show the node history."
            )
        db_connection = get_db_connection()
        list_node_kbbs = db_connection.kbn_search_by_id(self.data["kbn_id"])
        list_node_history = [
            KBB(kbb_id=kbb_id).__str__() for kbb_id in list_node_kbbs.keys()
        ]
        self.list_node_history = list_node_history
        print("\n".join(self.list_node_history))

    
    def show_kbb_history(self):
        """
        Display the history of the KBB entries related to this KBB.

        This method retrieves the previous KBB entries' IDs associated with this 
        KBB and constructs a visual representation of their history. It asserts 
        that the current KBB must be in a 'computed' state before displaying the 
        history.
        """
        assert self.data["state"] == "computed", \
            "To show the history of the KBB, you need to compute it."

        list_kbb_ids = [self.data["kbb_id"]]
        list_sentences = [self.__str__()]
        list_ids = [{"parent": self.data["kbb_id"], "child": c["kbb_id"]} for c in self.data["parents_kbb"]]

        while len(list_ids) > 0:
            pc = list_ids.pop(0)
            kbb = KBB(kbb_id=pc["child"])

            tmp_list_parents_pos = [index for index, value in enumerate(list_kbb_ids) if value == pc["parent"]]
            sentence = f'↑__ {kbb.__str__()}'

            for j, p in enumerate(tmp_list_parents_pos):
                list_kbb_ids.insert(p+j+1, pc["child"])
                n_white_spaces = len(list_sentences[p+j]) - len(list_sentences[p+j].lstrip())
                list_sentences.insert(p+j+1, " " * (n_white_spaces+5) + sentence)

            new_children = kbb.data["parents_kbb"]
            list_ids.extend([{"parent": pc["child"], "child": c["kbb_id"]} for c in new_children])

        self.list_kbb_history = [key for key, group in groupby(list_sentences)]
        self.list_kbb_history = fixed_length_list(
            list_strings=self.list_kbb_history, 
            l=100, 
            additional_space=4
        )
        print("\n".join(self.list_kbb_history))


    def build_graph(self):
        """
        Build a directed graph representing the history of the KBB.

        This method constructs a directed graph where each node represents a
        KBB, and edges represent the relationships between KBB entries,
        based on their parent-child relationships. It starts with the current 
        KBB and processes its parent KBBs recursively.

        Returns:
            None: This method does not return a value but updates the graph 
            property `self.g` to represent the history of KBB entries.
        """
        assert self.data["state"] == "computed", \
            "To build the history graph of the KBB, you need to compute it."
        list_nodes = [self.data["kbb_id"]]
        self.g = Graph(directed=True)
        self.g.add_vertex(
            name=self.data["kbb_id"], 
            node=self.data["kbn_id"],    
        )
        while len(list_nodes) > 0:
            kbb_id = list_nodes.pop(0)
            kbb = KBB(kbb_id=kbb_id)
            vertex_index = self.g.vs.select(name=kbb.data["kbb_id"])[0].index
            self.g.vs[vertex_index]["content"] = kbb.data["content"] 
            kbb_parents = kbb.data["parents_kbb"]
            for kbb_parent in kbb_parents:
                list_nodes.append(kbb_parent["kbb_id"])
                if len(self.g.vs.select(name=kbb_parent["kbb_id"])) == 0:
                    self.g.add_vertex(
                        name=kbb_parent["kbb_id"], 
                        node=kbb_parent["kbn_id"],
                    )
                if self.g.get_eid(kbb_parent["kbb_id"], kbb.data["kbb_id"], directed=True, error=False) == -1:
                    self.g.add_edge(
                        source=kbb_parent["kbb_id"], 
                        target=kbb.data["kbb_id"]
                    )

    
    def recompute(self) -> "KBB":
        """
        Recompute the KBB entry and its relationships.

        This method updates the KBB instance by re-evaluating its parent KBBs,
        adjusting timestamps and IDs as necessary. It ensures that all parent 
        KBBs are computed before making changes to the current KBB.

        Returns:
            KBB: A new KBB instance representing the latest state after 
            recomputation.
        """
        assert self.data["state"] == "computed", \
            "To recompute the KBB, you need to compute it first."
        list_kbb_ids = [self.data["kbb_id"]]
        list_kbbs = []
        dict_substitutions = {}
        while len(list_kbb_ids) > 0:
            kbb_id = list_kbb_ids.pop(0)
            kbb = KBB(kbb_id=kbb_id)
            list_kbbs.append(kbb)
            kbb_parents = kbb.data["parents_kbb"]
            for kbb_parent in kbb_parents:
                list_kbb_ids.append(kbb_parent["kbb_id"])
        list_kbbs.reverse()
        db_connection = get_db_connection()
        while len(list_kbbs) > 0:
            new_kbb = kbb = list_kbbs.pop(0)
            if len(kbb.data["parents_kbb"]) == 0:
                last_kbb_id = db_connection.kbn_get_last_kbb_id(kbn_id=kbb.data["kbn_id"])
                if kbb.data["kbb_id"] != last_kbb_id:
                    dict_substitutions[kbb.data["kbb_id"]] = last_kbb_id
                    new_kbb = KBB(kbb_id=last_kbb_id)
            else:
                new_parents_kbb = []
                bool_update_parent = False
                for parent_kbb in kbb.data["parents_kbb"]:
                    if parent_kbb["kbb_id"] in dict_substitutions.keys():
                        bool_update_parent = True
                        new_parents_kbb.append(
                            {
                                "kbb_id": dict_substitutions[parent_kbb["kbb_id"]], 
                                "kbn_id": parent_kbb["kbn_id"]
                            }
                        )
                    else:
                        new_parents_kbb.append(parent_kbb)
                if bool_update_parent:
                    new_kbb = KBB(
                        kbb_data={
                            "kbn_id": kbb.data["kbn_id"], 
                            "parents_op": kbb.data["parents_op"],
                            "parents_kbb": new_parents_kbb
                        }
                    )
                    new_kbb.compute()
                    dict_substitutions[kbb.data["kbb_id"]] = new_kbb.data["kbb_id"]
        return new_kbb
                

def fixed_length_list(
        list_strings: List[str], 
        l: int=100, 
        additional_space: int=4
    ) -> List[str]:
    """
    Adjust a list of strings to ensure fixed length output.

    This function processes a list of strings, ensuring that each string
    fits within a specified length. If a string exceeds this length, 
    it will be split, and leading white space will be accounted for.
    If the total space (initial whitespace plus additional space) 
    results in a string that cannot fit, an ellipsis ("[...]") is appended 
    to the list.

    Args:
        list_strings (list): A list of strings to be processed.
        l (int, optional): The maximum length for each string. 
            Defaults to 100.
        additional_space (int, optional): The additional spaces to 
            prepend for formatting. Defaults to 4.

    Returns:
        list: A new list containing the adjusted strings, each fitting
            within the specified length. If a string exceeds the maximum 
            length and cannot be adjusted, it adds "[...]".
    """
    new_list = []
    for _, row in enumerate(list_strings):
        initial_white_space = len(row) - len(row.lstrip())
        total_space = (initial_white_space + additional_space) * " "
        if len(total_space) >= l-20:
            new_list.append("[...]")
            break
        tmp = row
        while len(tmp) > l:
            new_list.append(tmp[:l])
            if _ > 0:
                tmp =  total_space + tmp[l:]
            else:
                tmp = tmp[l:]
        new_list.append(tmp)
    return new_list

                

