import os
from chromadb import HttpClient # type: ignore
from chromadb.utils.embedding_functions import ( # type: ignore
    OpenAIEmbeddingFunction
)
from ast import literal_eval
from copy import deepcopy
from typing import List, Any
from ..log import logger
from .db import DatabaseConnection


class ChromaDBConnection(DatabaseConnection):
    """
    ChromaDBConnection class to interface with a Chroma database.

    This class extends the DatabaseConnection abstract base class and provides 
    implementations for various methods to manage knowledge base docs (KBD), 
    knowledge base node (KBN), and knowledge base blocks (KBB). 
    It establishes a connection to the Chroma database.
    """

    def __init__(self):
        """
        Initialize the ChromaDBConnection instance.

        This constructor creates an HttpClient to connect to the Chroma 
        database using the host and port specified in environment variables. 
        It also initializes the OpenAI embedding function for generating text 
        embeddings. Additionally, it ensures that the KBD, KBN and KBB 
        collections exist in the database.
        """
        self.client = HttpClient(
            host=os.getenv('CHROMA_DB_HOST'), 
            port=os.getenv('CHROMA_DB_PORT')
        )
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key=os.getenv('OPENAI_API_KEY'), 
            model_name=os.getenv('CHROMA_EMBEDDING_MODEL')
        )
        self.kbd_create_collection_if_not_exists()
        self.kbn_create_collection_if_not_exists()
        self.kbb_create_collection_if_not_exists()
        logger.debug("ChromaDB client ready.")

    '''KBD'''

    def kbd_exists_collection(self) -> bool:
        """
        Check if the KBD collection exists in the database.

        Returns:
            bool: True if the KBD collection exists, False otherwise.
        """
        return "KBD" in [_.name for _ in self.client.list_collections()]

    def kbd_create_collection(self):
        """
        Create a new KBD collection in the database.
        """
        self.client.create_collection("KBD")
        logger.debug(f"Collection KBD created.")

    def kbd_update(self, kbd: Any):
        """
        Update an existing KBD entry in the database.

        This method prepares the KBD data for updating and sends it to the KBD 
        collection.

        Args:
            kbd: The KBD object containing the data to be updated.
        """
        collection = self.client.get_collection("KBD")
        kbd = deepcopy(kbd)
        del kbd.data["kbbs"]
        kbd.data["operations"] = str(kbd.data["operations"])
        kbd.data["kbb_ids"] = str(kbd.data["kbb_ids"])
        collection.upsert(
            ids=[kbd.data["kbd_id"]], 
            documents=[""],
            embeddings=[[0]],
            metadatas=[kbd.data]
        )
        logger.debug(f"KBD {kbd.data['kbd_id']} updated.")

    def kbd_search_by_id(self, kbd_id: str) -> dict:
        """
        Search for a KBD entry by its ID.

        Args:
            kbd_id (str): The ID of the KBD entry to be searched.

        Returns:
            dict: The KBD entry's metadata if found, 
                otherwise an empty dictionary.
        """
        collection = self.client.get_collection("KBD")
        results = collection.get(
            ids=[kbd_id],
            include=['metadatas']
        )
        if len(results["ids"]) > 0:
            logger.debug(f"KBD {kbd_id} found.")
            output = results["metadatas"][0]
            output["kbd_id"] = kbd_id
            output["kbb_ids"] = literal_eval(output["kbb_ids"])
            output["operations"] = literal_eval(output["operations"])
            return output
        logger.debug(f"KBD {kbd_id} not found.")
        return {}

    '''KBN'''

    def kbn_exists_collection(self) -> bool:
        """
        Check if the KBN collection exists in the database.

        Returns:
            bool: True if the KBN collection exists, False otherwise.
        """
        return "KBN" in [_.name for _ in self.client.list_collections()]

    def kbn_create_collection(self):
        """
        Create a new KBN collection in the database.
        """        
        self.client.create_collection("KBN")
        logger.debug(f"Collection KBN created.")

    def kbn_create(self, kbn_id: str, kbb_id: str, kbb_tms: float):
        """
        Create a new KBN entry with an associated KBB.

        Args:
            kbn_id: The ID of the new KBN entry.
            kbb_id: The ID of the associated KBB.
            kbb_tms: The timestamp of the associated KBB.
        """
        collection = self.client.get_collection("KBN")
        collection.add(
            ids=[kbn_id], 
            documents=[""],
            embeddings=[[0]],
            metadatas=[{kbb_id: kbb_tms}],
        )
        logger.debug(f"KBN {kbn_id} created with one KBB {kbb_id} computed at {kbb_tms}.")

    def kbn_search_by_id(self, kbn_id: str) -> dict:
        """
        Search for a KBN entry by its ID.

        Args:
            kbn_id (str): The ID of the KBN entry to be searched.

        Returns:
            dict: The KBN entry's metadata if found, 
                otherwise an empty dictionary.
        """
        collection = self.client.get_collection("KBN")
        results = collection.get(
            ids=[kbn_id],
            include=['metadatas']
        )
        if len(results["ids"]) > 0:
            logger.debug(f"KBN {kbn_id} found.")
            return results["metadatas"][0]
        logger.debug(f"KBN {kbn_id} not found.")
        return {}

    def kbn_add_new_kbb(self, kbn_id: str, kbb_id: str, kbb_tms: float):
        """
        Add a new KBB entry to an existing KBN entry.

        This method retrieves the current metadata of the KBN entry 
        and updates it with a new KBB ID and timestamp.

        Args:
            kbn_id (str): The ID of the KBN entry to be updated.
            kbb_id (str): The ID of the new KBB to add.
            kbb_tms (float): The timestamp of the new KBB.
        """
        old_metadatas = self.kbn_search_by_id(kbn_id)
        new_metadata = {**old_metadatas, kbb_id: kbb_tms}
        collection = self.client.get_collection("KBN")
        collection.update(
            ids=[kbn_id],
            metadatas=[new_metadata]
        )

    def kbn_get_last_kbb_id(self, kbn_id: str) -> str:
        """
        Retrieve the ID of the last added KBB entry for a given KBN.

        This method searches for existing KBBs associated with a given 
        KBN ID and returns the KBB ID that has the latest timestamp.

        Args:
            kbn_id (str): The ID of the KBN entry.

        Returns:
            str: The ID of the last KBB entry associated with the given KBN.
        """
        dict_kbbs = self.kbn_search_by_id(kbn_id)
        if len(dict_kbbs):
            max_key = max(dict_kbbs, key=lambda k: float(str(dict_kbbs.get(k))))
            return max_key
        return ""

    '''KBB'''

    def kbb_exists_collection(self) -> bool:
        """
        Check if the KBB collection exists in the database.

        Returns:
            bool: True if the KBB collection exists, False otherwise.
        """
        return "KBB" in [_.name for _ in self.client.list_collections()]

    def kbb_create_collection(self):
        """
        Create a new KBB collection in the database.
        """
        self.client.create_collection("KBB")
        logger.debug(f"Collection KBB created.")

    def kbb_create(self, kbb: Any):
        """Add a new KBB entry to the KBB collection.

        This method adds a KBB entry, including its content and associated 
        metadata to the KBB collection in the database.

        Args:
            kbb (KBB): The KBB object containing the data to be added.
        """
        collection = self.client.get_collection("KBB")
        collection.add(
            ids=[kbb.data["kbb_id"]], 
            documents=[kbb.data["content"]],
            embeddings=[kbb.data["embedding"]],
            metadatas=[{key: str(value) for key, value in kbb.data.items() if key not in ["embedding"]}],
        )
        logger.debug(f"{kbb.data['kbb_id']} added.")
    
    def kbb_search_by_id(self, kbb_id: str) -> dict:
        """
        Search for a KBB entry by its ID.

        Args:
            kbb_id (str): The ID of the KBB entry to be searched.

        Returns:
            dict: The KBB entry's data if found, otherwise an empty dictionary.
        """
        collection = self.client.get_collection("KBB")
        results = collection.get(
            ids=[kbb_id],
            include=['embeddings', 'documents', 'metadatas']
        )
        if len(results["ids"]) > 0:
            kbb_data = results["metadatas"][0].copy()
            kbb_data["embedding"] = results["embeddings"][0]
            kbb_data["parents_kbb"] = literal_eval(kbb_data["parents_kbb"])
            kbb_data["tms_create"] = float(kbb_data["tms_create"])
            kbb_data["tms_compute"] = float(kbb_data["tms_compute"])
            return kbb_data
        logger.debug(f"KBB {kbb_id} not found")
        return {}

    def kbb_search_by_text(
        self, 
        text: str, 
        kbb_ids_to_query: List[str] = [], 
        distance: float = 1.0, 
        n_results: int = 10
    ) -> list:
        """
        Search for KBB entries that match the given text.

        This method generates an embedding for the input text and queries the 
        KBB collection to find entries that are semantically similar based on 
        the computed embedding. The results are filtered based on the specified 
        distance threshold, and a limited number of results can be returned.

        Args:
            text (str): The input text to search for in the KBB collection.
            kbb_ids_to_query (list, optional): A list of KBB IDs to narrow down 
                the search. If empty, all KBB entries will be considered. 
                Defaults to an empty list.
            distance (float, optional): The maximum distance allowable for an 
                entry to be considered a match. Defaults to 1.0 (lower values 
                are stricter).
            n_results (int, optional): The maximum number of results to return. 
                Defaults to 10.

        Returns:
            list: A list of tuples, each containing the distance to the matching 
                KBB entry and the corresponding KBB entry. If no matches are 
                found, an empty list is returned.
        """
        query_embedding = self.embedding_function([text])
        collection = self.client.get_collection("KBB")
        where_clause = {} if len(kbb_ids_to_query) == 0 \
            else {"kbb_id": {"$in": kbb_ids_to_query}}
        results = collection.query(
            query_embeddings=query_embedding, 
            n_results=n_results, 
            include=["documents", "metadatas", "distances", "embeddings"], 
            where=where_clause
        )
        list_kbb_data = []
        list_distances = []
        for _ in range(len(results["ids"][0])):
            if results["distances"][0][_] <= distance:
                kbb_data = results["metadatas"][0][_].copy()
                kbb_data["embeddings"] = results["embeddings"][0][_]
                kbb_data["parents_kbb"] = literal_eval(kbb_data["parents_kbb"])
                kbb_data["tms_create"] = float(kbb_data["tms_create"])
                kbb_data["tms_compute"] = float(kbb_data["tms_compute"])
                list_kbb_data.append(kbb_data)
                list_distances.append(results["distances"][0][_])
        if len(list_kbb_data) > 0:
            tmp = sorted(zip(list_distances, range(len(list_distances)), list_kbb_data))
            list_output = [(d, kbb_data) for d, _, kbb_data in tmp]
            logger.debug(f"Found {len(list_output)} KBBs.")
            return list_output
        else:
            logger.debug(f"Found 0 KBB.")
            return []

