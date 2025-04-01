from dataclasses import dataclass
import logging
import sqlite3
from typing import Any, List

from boxing.utils.sql_utils import get_db_connection
from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Boxer:
    """
    A class to manage boxers.

    Attributes:
        id (int): Id of boxer.
        name (str): Name of boxer.
        weight (int): Weight of boxer.
        reach (float): Reach of boxer.
        age (int): Age of boxer.

    """
    id: int
    name: str
    weight: int
    height: int
    reach: float
    age: int
    weight_class: str = None

    def __post_init__(self):
        """

        Initialize via assigning weight classes.

        """
        self.weight_class = get_weight_class(self.weight)  # Automatically assign weight class


def create_boxer(name: str, weight: int, height: int, reach: float, age: int) -> None:
    """
    Creates a new boxer in the database.
    
    Args:
        name (str): Name of boxer.
        weight (int): Weight (lbs).
        height (int): Height (inches).
        reach (float): Reach (inches).
        age (int): Age (years).

    Raises:
        ValueError: If the inputs are invalid or boxer already exists.
        sqlite3.Error: If database error occurs.
    """
    logger.info(f"Attempting to create boxer: {name}")

    if weight < 125:
        logger.warning(f"Invalid weight: {weight}")
        raise ValueError(f"Invalid weight: {weight}. Must be at least 125.")
    if height <= 0:
        logger.warning(f"Invalid height: {height}")
        raise ValueError(f"Invalid height: {height}. Must be greater than 0.")
    if reach <= 0:
        logger.warning(f"Invalid reach: {reach}")
        raise ValueError(f"Invalid reach: {reach}. Must be greater than 0.")
    if not (18 <= age <= 40):
        logger.warning(f"Invalid age: {age}")
        raise ValueError(f"Invalid age: {age}. Must be between 18 and 40.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the boxer already exists (name must be unique)
            cursor.execute("SELECT 1 FROM boxers WHERE name = ?", (name,))
            if cursor.fetchone():
                raise ValueError(f"Boxer with name '{name}' already exists")

            cursor.execute("""
                INSERT INTO boxers (name, weight, height, reach, age)
                VALUES (?, ?, ?, ?, ?)
            """, (name, weight, height, reach, age))

            conn.commit()
            logger.info(f"Successfully created boxer: {name}")

    except sqlite3.IntegrityError:
        logger.error(f"Boxer with name '{name}' already exists")
        raise ValueError(f"Boxer with name '{name}' already exists")

    except sqlite3.Error as e:
        logger.exception("Database error during boxer creation")
        raise e


def delete_boxer(boxer_id: int) -> None:
    """
    Deletes a boxer from the databse.

    Args: boxer_id (int): The ID of the boxer to delete.

    Raieses: 
        ValueError: If boxer not found.
        sqlite.Error: If database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning(f"Boxer not found while trying to delete")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            cursor.execute("DELETE FROM boxers WHERE id = ?", (boxer_id,))
            conn.commit()
            logger.info(f"Successfully delelted boxer ID: {boxer_id}")

    except sqlite3.Error as e:
        logger.exception(f"Database error while trying to delete")
        raise e


def get_leaderboard(sort_by: str = "wins") -> List[dict[str, Any]]:
    """
    Retrieves the leaderboard sorted by win/win percentages.

    Args: 
        sort_by (str): Either wins or win_pct.

    Returns:
        List[dict[str, Any]]: List of boxer stats.

    Raises:
        ValueError: if sort_by value is invalid.
        sqlite3.Error: if database error occurs.
    """
    logger.info(f"Getting leaderboard sorted by: {sort_by}")
    query = """
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.warning(f"Invalid sort_by parameters while fetching leaderboard")
        raise ValueError(f"Invalid sort_by parameter: {sort_by}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        leaderboard = []
        for row in rows:
            boxer = {
                'id': row[0],
                'name': row[1],
                'weight': row[2],
                'height': row[3],
                'reach': row[4],
                'age': row[5],
                'weight_class': get_weight_class(row[2]),  # Calculate weight class
                'fights': row[6],
                'wins': row[7],
                'win_pct': round(row[8] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(boxer)

        return leaderboard

    except sqlite3.Error as e:
        logger.exception("Database error while fetching leaderboard")
        raise e


def get_boxer_by_id(boxer_id: int) -> Boxer:
    """
    Fetches a boxer from the database by ID

    Args: 
        boxer_id (int): The boxer ID

    Returns:
        Boxer: The matching boxer object

    Raises:
        ValueError: If boxer cannot be found
        sqlite3.Error: If database error occurs
    """
    logger.info(f"Fetching boxer by ID: {boxer_id}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE id = ?
            """, (boxer_id,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                return boxer
            else:
                logger.warning(f"Boxer with id not found while trying to match boxer to id")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

    except sqlite3.Error as e:
        logger.exception("Database error while trying to match boxer to id")
        raise e


def get_boxer_by_name(boxer_name: str) -> Boxer:
    """
    Fetches boxer via name.

    Args:
        boxer_name (str): Name of boxer.
    
    Returns:
        Boxer: Matching boxer object.

    Raises:
        ValueError: If boxer not found
        sqlite3.Error: If database error occurs
    """
    logger.info("Fetching boxer by name")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE name = ?
            """, (boxer_name,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                return boxer
            else:
                logger.warning("Boxer not found while trying to match boxer to name")
                raise ValueError(f"Boxer '{boxer_name}' not found.")

    except sqlite3.Error as e:
        logger.exception("Database error while trying to match boxer to name")
        raise e


def get_weight_class(weight: int) -> str:
    """
    Determines weight class based on weight

    Args:
        weight (int): Weight (lbs)

    Returns:
        weight_class: str of weight class divisions

    Raises:
        ValueError: If weight is below the minimum 
    """
    if weight >= 203:
        weight_class = 'HEAVYWEIGHT'
    elif weight >= 166:
        weight_class = 'MIDDLEWEIGHT'
    elif weight >= 133:
        weight_class = 'LIGHTWEIGHT'
    elif weight >= 125:
        weight_class = 'FEATHERWEIGHT'
    else:
        raise ValueError(f"Invalid weight: {weight}. Weight must be at least 125.")

    return weight_class


def update_boxer_stats(boxer_id: int, result: str) -> None:
    """
    Updates a boxer's statistics

    Args:
        boxer_id (int): ID of boxer
        result (str): win or loss

    Raises:
        ValueError: If result is invalid or boxer can't be found
        sqlite3.Error: If database error occurs
    """
    logger.info(f"Updating boxer stats with results")
    if result not in {'win', 'loss'}:
        logger.warning("Invalid result for updating")
        raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning("Boxer with ID not found for updating purposes")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            if result == 'win':
                cursor.execute("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?", (boxer_id,))
            else:  # result == 'loss'
                cursor.execute("UPDATE boxers SET fights = fights + 1 WHERE id = ?", (boxer_id,))

            conn.commit()
            logger.info("Successfully updated states for boxer")

    except sqlite3.Error as e:
        logger.exception("Database error occurred during stat update")
        raise e
