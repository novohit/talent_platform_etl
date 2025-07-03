from elasticsearch import Elasticsearch
from typing import Dict, Any, List, Optional
import json
from pathlib import Path

from elasticsearch.exceptions import NotFoundError
from config import config
from logger import logger


def get_es_client() -> Elasticsearch:
    """
    Get Elasticsearch client instance
    """
    return Elasticsearch(
        hosts=config.ES_HOSTS,
        basic_auth=(config.ES_USERNAME, config.ES_PASSWORD)
        if config.ES_USERNAME
        else None,
        timeout=config.ES_TIMEOUT,
    )


class ESClient:
    def __init__(self):
        self.client = get_es_client()
        self.mappings_dir = Path(__file__).parent / "mappings"
        logger.info("ESClient initialized with hosts: %s", config.ES_HOSTS)

    def load_mapping(self, mapping_file: str) -> Dict[str, Any]:
        """
        Load index mapping configuration from JSON file

        Args:
            mapping_file: Name of the mapping file

        Returns:
            Mapping configuration dictionary

        Raises:
            FileNotFoundError: Mapping file does not exist
            json.JSONDecodeError: Invalid mapping file format
        """
        file_path = self.mappings_dir / f"{mapping_file}"
        if not file_path.exists():
            logger.error("Mapping file not found: %s", file_path)
            raise FileNotFoundError(f"Mapping file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                mapping = json.load(f)
                logger.info("Successfully loaded mapping from file: %s", file_path)
                return mapping
        except json.JSONDecodeError as e:
            logger.error("Failed to parse mapping file %s: %s", file_path, str(e))
            raise

    def create_index(
        self,
        index: str,
        mapping: Optional[Dict[str, Any]] = None,
        mapping_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create index and set mapping

        Args:
            index: Index name
            mapping: Mapping definition dictionary (choose either this or mapping_file)
            mapping_file: Mapping file name (choose either this or mapping)

        Returns:
            Creation result

        Raises:
            ValueError: Neither mapping nor mapping_file provided, or both provided
        """
        if mapping is None and mapping_file is None:
            logger.error(
                "Neither mapping nor mapping_file provided for index: %s", index
            )
            raise ValueError("Either mapping or mapping_file must be provided")
        if mapping is not None and mapping_file is not None:
            logger.error("Both mapping and mapping_file provided for index: %s", index)
            raise ValueError("Cannot provide both mapping and mapping_file")

        try:
            if mapping_file is not None:
                mapping = self.load_mapping(mapping_file)
                logger.info(
                    "Creating index %s with mapping from file: %s", index, mapping_file
                )
            else:
                logger.info("Creating index %s with provided mapping", index)

            response = self.client.indices.create(index=index, body=mapping)
            logger.info("Successfully created index: %s", index)
            return response.body
        except Exception as e:
            logger.error("Failed to create index %s: %s", index, str(e))
            raise

    def delete_index(self, index: str) -> Dict[str, Any]:
        """
        Delete index

        Args:
            index: Index name

        Returns:
            Deletion result

        Raises:
            Exception: Failed to delete index
        """
        try:
            logger.info("Deleting index: %s", index)
            response = self.client.indices.delete(index=index)
            logger.info("Successfully deleted index: %s", index)
            return response.body
        except Exception as e:
            if isinstance(e, NotFoundError):
                logger.warning("Index %s does not exist", index)
                return {"acknowledged": True}
            logger.error("Failed to delete index %s: %s", index, str(e))
            raise

    def search(
        self,
        index: str,
        query: Dict[str, Any],
        source: Optional[List[str]] = None,
        size: int = 10,
        from_: int = 0,
    ) -> Dict[str, Any]:
        """
        Execute Elasticsearch query

        Args:
            index: Index name
            query: Query DSL
            source: List of fields to return, None means return all fields
            size: Number of documents to return
            from_: Starting position for pagination

        Returns:
            Query results
        """
        try:
            body = {"query": query, "size": size, "from": from_}
            if source is not None:
                body["_source"] = source

            logger.debug("Searching in index %s with query: %s", index, query)
            response = self.client.search(index=index, body=body)
            logger.debug(
                "Search completed in index %s, found %d hits",
                index,
                response.body.get("hits", {}).get("total", {}).get("value", 0),
            )
            return response.body
        except Exception as e:
            logger.error("Search failed in index %s: %s", index, str(e))
            raise

    def get_by_id(
        self, index: str, doc_id: str, source: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get document by ID

        Args:
            index: Index name
            doc_id: Document ID
            source: List of fields to return, None means return all fields

        Returns:
            Document content
        """
        try:
            params = {}
            if source is not None:
                params["_source"] = source

            logger.debug("Getting document %s from index %s", doc_id, index)
            response = self.client.get(index=index, id=doc_id, **params)
            logger.debug(
                "Successfully retrieved document %s from index %s", doc_id, index
            )
            return response.body
        except Exception as e:
            logger.error(
                "Failed to get document %s from index %s: %s", doc_id, index, str(e)
            )
            raise

    def delete_by_query(self, index: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete documents by query

        Args:
            index: Index name
            query: Query DSL

        Returns:
            Deletion result
        """
        try:
            logger.info("Deleting documents from index %s with query: %s", index, query)
            response = self.client.delete_by_query(index=index, body=query)
            logger.info(
                "Successfully deleted %d documents from index %s",
                response.body.get("deleted", 0),
                index,
            )
            return response.body
        except Exception as e:
            logger.error("Failed to delete documents from index %s: %s", index, str(e))
            raise

    def update_by_query(
        self, index: str, query: Dict[str, Any], script: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update documents by query

        Args:
            index: Index name
            query: Query DSL
            script: Update script

        Returns:
            Update result
        """
        try:
            body = {"query": query, "script": script}
            logger.info("Updating documents in index %s with query: %s", index, query)
            response = self.client.update_by_query(index=index, body=body)
            logger.info(
                "Successfully updated %d documents in index %s",
                response.body.get("updated", 0),
                index,
            )
            return response.body
        except Exception as e:
            logger.error("Failed to update documents in index %s: %s", index, str(e))
            raise

    def bulk(self, index: str, operations: List[Dict[str, Any]]) -> int:
        """
        Execute bulk operations

        Args:
            operations: List of bulk operation request bodies, each operation is a dictionary
                      containing operation type (index, create, update, delete) and corresponding data
            index: Optional default index name

        Returns:
            Bulk operation result
        """
        try:
            logger.info("Executing bulk operation with %d items", len(operations))
            from elasticsearch.helpers import bulk, BulkIndexError

            success_count, _ = bulk(self.client, operations, index=index)
            logger.info(
                "Bulk operation completed: %d/%d items succeeded",
                success_count,
                len(operations),
            )
            return success_count
        except BulkIndexError as e:
            logger.error(
                "Bulk operation failed: %d document(s) failed to index", len(e.errors)
            )
            logger.error("Document error: %s", e.errors[0])
            # raise
        except Exception as e:
            logger.error("Bulk operation failed: %s", str(e))
            raise


es_client = ESClient()
