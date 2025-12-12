#!/usr/bin/env python
"""
Oracle-Meilisearch Sync CLI

Main entry point for the Oracle-Meilisearch synchronization tool.
"""
import sys
import argparse
import logging
from pathlib import Path

from src.config import load_dotenv, get_oracle_config, get_meilisearch_config, ConfigError
from src.sync_engine import SyncEngine
from src.scheduler import Scheduler, CronScheduler


def setup_logging(log_level):
    """Configure logging for the application.

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_config(env_file=None):
    """Load configuration from environment variables or .env file.

    Args:
        env_file (str, optional): Path to .env file

    Returns:
        tuple: (oracle_config, meilisearch_config)

    Raises:
        ConfigError: If required configuration is missing
    """
    # Load .env file if specified or if default .env exists
    if env_file:
        load_dotenv(env_file)
    else:
        default_env = Path('.env')
        if default_env.exists():
            load_dotenv(str(default_env))

    try:
        oracle_config = get_oracle_config()
        meilisearch_config = get_meilisearch_config()
        return oracle_config, meilisearch_config
    except ConfigError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        print("\nPlease ensure all required environment variables are set.", file=sys.stderr)
        print("You can use a .env file (see .env.example for reference).", file=sys.stderr)
        sys.exit(1)


def cmd_full_sync(args):
    """Execute full synchronization.

    Args:
        args: Parsed command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting full synchronization...")
    logger.info(f"Table: {args.table}")
    logger.info(f"Primary Key: {args.primary_key}")
    logger.info(f"Index Name: {args.index or args.table}")
    logger.info(f"Recreate Index: {args.recreate}")

    # Load configuration
    oracle_config, meilisearch_config = load_config(args.env_file)

    # Create sync engine
    sync_engine = SyncEngine(oracle_config, meilisearch_config)

    # Perform full sync
    try:
        result = sync_engine.full_sync(
            table_name=args.table,
            primary_key=args.primary_key,
            index_name=args.index or args.table,
            recreate_index=args.recreate
        )

        if result['success']:
            logger.info("Full synchronization completed successfully!")
            logger.info(f"Oracle records: {result['oracle_count']}")
            logger.info(f"Meilisearch documents: {result['meilisearch_count']}")

            # Save sync state if requested
            if args.save_state:
                sync_engine.persist_sync_state(args.state_file)
                logger.info(f"Sync state saved to {args.state_file}")
        else:
            logger.error("Full synchronization failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during full sync: {e}", exc_info=True)
        sys.exit(1)


def cmd_incremental_sync(args):
    """Execute incremental synchronization.

    Args:
        args: Parsed command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting incremental synchronization...")
    logger.info(f"Table: {args.table}")
    logger.info(f"Primary Key: {args.primary_key}")
    logger.info(f"Modified Column: {args.modified_column}")
    logger.info(f"Index Name: {args.index or args.table}")

    # Load configuration
    oracle_config, meilisearch_config = load_config(args.env_file)

    # Create sync engine
    sync_engine = SyncEngine(oracle_config, meilisearch_config)

    # Load previous sync state if available
    if Path(args.state_file).exists():
        sync_engine.load_sync_state(args.state_file)
        logger.info(f"Loaded sync state from {args.state_file}")

    # Perform incremental sync
    try:
        result = sync_engine.incremental_sync(
            table_name=args.table,
            primary_key=args.primary_key,
            modified_column=args.modified_column,
            index_name=args.index or args.table,
            soft_delete_column=args.soft_delete_column
        )

        if result['success']:
            logger.info("Incremental synchronization completed successfully!")
            logger.info(f"Changed records: {result['changed_count']}")

            # Save sync state
            sync_engine.persist_sync_state(args.state_file)
            logger.info(f"Sync state saved to {args.state_file}")
        else:
            logger.error("Incremental synchronization failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during incremental sync: {e}", exc_info=True)
        sys.exit(1)


def cmd_schedule(args):
    """Start scheduled incremental synchronization.

    Args:
        args: Parsed command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting scheduled synchronization...")
    logger.info(f"Table: {args.table}")
    logger.info(f"Primary Key: {args.primary_key}")
    logger.info(f"Modified Column: {args.modified_column}")
    logger.info(f"Interval: {args.interval} seconds")

    # Load configuration
    oracle_config, meilisearch_config = load_config(args.env_file)

    # Create sync engine
    sync_engine = SyncEngine(oracle_config, meilisearch_config)

    # Load previous sync state if available
    if Path(args.state_file).exists():
        sync_engine.load_sync_state(args.state_file)
        logger.info(f"Loaded sync state from {args.state_file}")

    # Create scheduler
    scheduler = Scheduler(sync_engine, args.interval)

    try:
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        scheduler.start()

        # Keep main thread alive
        import time
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.stop()
        logger.info("Scheduler stopped.")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Oracle-Meilisearch Synchronization Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full sync
  python -m src.main full-sync --table USERS --primary-key ID

  # Incremental sync
  python -m src.main incremental-sync --table USERS --primary-key ID --modified-column UPDATED_AT

  # Scheduled sync (every 5 minutes)
  python -m src.main schedule --table USERS --primary-key ID --modified-column UPDATED_AT --interval 300

  # Using custom .env file
  python -m src.main full-sync --table USERS --primary-key ID --env-file /path/to/.env
        """
    )

    # Global options
    parser.add_argument(
        '--env-file',
        help='Path to .env file (default: .env in current directory)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Full sync command
    full_sync_parser = subparsers.add_parser(
        'full-sync',
        help='Perform full synchronization from Oracle to Meilisearch'
    )
    full_sync_parser.add_argument(
        '--table',
        required=True,
        help='Oracle table name to sync'
    )
    full_sync_parser.add_argument(
        '--primary-key',
        required=True,
        help='Primary key column name'
    )
    full_sync_parser.add_argument(
        '--index',
        help='Meilisearch index name (default: same as table name)'
    )
    full_sync_parser.add_argument(
        '--recreate',
        action='store_true',
        help='Recreate Meilisearch index before sync'
    )
    full_sync_parser.add_argument(
        '--save-state',
        action='store_true',
        help='Save sync state after completion'
    )
    full_sync_parser.add_argument(
        '--state-file',
        default='sync_state.json',
        help='Sync state file path (default: sync_state.json)'
    )
    full_sync_parser.set_defaults(func=cmd_full_sync)

    # Incremental sync command
    incremental_sync_parser = subparsers.add_parser(
        'incremental-sync',
        help='Perform incremental synchronization (only changed records)'
    )
    incremental_sync_parser.add_argument(
        '--table',
        required=True,
        help='Oracle table name to sync'
    )
    incremental_sync_parser.add_argument(
        '--primary-key',
        required=True,
        help='Primary key column name'
    )
    incremental_sync_parser.add_argument(
        '--modified-column',
        required=True,
        help='Modified timestamp column name'
    )
    incremental_sync_parser.add_argument(
        '--index',
        help='Meilisearch index name (default: same as table name)'
    )
    incremental_sync_parser.add_argument(
        '--soft-delete-column',
        help='Soft delete flag column name (optional)'
    )
    incremental_sync_parser.add_argument(
        '--state-file',
        default='sync_state.json',
        help='Sync state file path (default: sync_state.json)'
    )
    incremental_sync_parser.set_defaults(func=cmd_incremental_sync)

    # Schedule command
    schedule_parser = subparsers.add_parser(
        'schedule',
        help='Start scheduled incremental synchronization'
    )
    schedule_parser.add_argument(
        '--table',
        required=True,
        help='Oracle table name to sync'
    )
    schedule_parser.add_argument(
        '--primary-key',
        required=True,
        help='Primary key column name'
    )
    schedule_parser.add_argument(
        '--modified-column',
        required=True,
        help='Modified timestamp column name'
    )
    schedule_parser.add_argument(
        '--index',
        help='Meilisearch index name (default: same as table name)'
    )
    schedule_parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Sync interval in seconds (default: 300 = 5 minutes)'
    )
    schedule_parser.add_argument(
        '--soft-delete-column',
        help='Soft delete flag column name (optional)'
    )
    schedule_parser.add_argument(
        '--state-file',
        default='sync_state.json',
        help='Sync state file path (default: sync_state.json)'
    )
    schedule_parser.set_defaults(func=cmd_schedule)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
