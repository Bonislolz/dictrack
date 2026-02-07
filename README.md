# dictrack - the dictionary tracker

<img src="https://img.shields.io/pypi/pyversions/dictrack.svg?color=%2334D058" alt="Supported Python versions">

## A Flexible Dictionary Data Tracker for Condition-Based Monitoring

`dictrack` is a powerful dictionary tracking tool designed for condition-based monitoring and management. At its core, `dictrack` allows developers to easily track and handle dynamic data using flexible components such as conditions, targets, and limiters. It supports various data sources (e.g., `Redis`, `MongoDB`) and offers advanced mechanisms for data caching and persistence.

## Features
- **Multi-Target Support**: Track multiple targets simultaneously with customizable logic.
- **Condition-Based Filtering**: Easily define conditions like key existence, value comparisons, or custom rules.
- **Flexible Limiting**: Use built-in limiters such as `CountLimiter` or `TimeLimiter` to control task execution.
- **Data Caching & Persistence**: Integrate `Redis` for caching and `MongoDB` for long-term storage.
- **Event System**: Includes events like `LIMITED`, `STAGE_COMPLETED`, and `ALL_COMPLETED` for fine-grained tracking.
- **Extensible Design**: Add custom conditions, targets, or limiters to adapt to unique requirements.
- **Python 2 & 3 Compatibility**: Seamlessly supports both Python 2.7 and 3.7+ environments.

## Getting Started

### Installation
Install the latest version of `dictrack` via pip:

```bash
pip install dictrack
```

If you need additional components, you can install `dictrack` with optional dependencies:

#### `Redis` support: For caching data using `redis-py`.

```bash
pip install dictrack[redis]
```

#### `MongoDB` support: For persistent storage using `pymongo`.

```bash
pip install dictrack[mongodb]
```

#### `Gevent` support: For asynchronous task execution with `gevent`.

```bash
pip install dictrack[gevent]
```

#### In-Memory support: For lightweight memory-based caching with `sortedcontainers`.

```bash
pip install dictrack[memory]
```

### Basic Usage
Here’s a simple example to get you started:

```python
from dictrack.conditions.keys import KeyValueEQ
from dictrack.data_caches.redis import RedisDataCache
from dictrack.data_stores.mongodb import MongoDBDataStore
from dictrack.manager import TrackingManager
from dictrack.trackers.numerics.count import CountTracker

# Initialize tracker manager
manager = TrackingManager(
    RedisDataCache(host="redis"),
    MongoDBDataStore(host="mongodb"),
)

# Add a tracker with conditions
tracker = CountTracker(
    name="Demo-1",
    conditions=[KeyValueEQ(key="status", value="active")],
    target=10,
)
group_id = "Robot001"
manager.add_tracker(group_id=group_id, tracker=tracker)

# Feed data into the manager
data = {"id": 1, "status": "active"}
# Process data based on the condition
manager.track(group_id=group_id, data=data)

# Check results
print(manager.get_trackers(group_id=group_id, name="Demo-1"))
>>>[<CountTracker (target=10 conditions=set([<KeyValueEQ (key=status operator=eq value=active)>]) limiters=set([]) group_id=Robot001 name=Demo-1 progress=1)>]
```
# Documentation

To build the documentation locally, you can use the provided script:

1.  Ensure you have the required dependencies installed:
    ```bash
    pip install .[docs]
    ```

2.  Run the documentation build script:
    ```bash
    ./docs.sh
    ```
    This script will:
    -   Install the package in editable mode.
    -   Generate API documentation source files using `sphinx-apidoc`.
    -   Build the HTML documentation using Sphinx.
    -   Start a local server to preview the documentation at `http://localhost:8000`.

The documentation is built using [Sphinx](https://www.sphinx-doc.org/) and hosted on [Read the Docs](https://dictrack.readthedocs.io/).

# Contributing

<a href="https://github.com/Bonislolz/dictrack/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Bonislolz/dictrack" />
</a>

# License
This project is licensed under the [MIT License](https://github.com/Bonislolz/dictrack?tab=MIT-1-ov-file).

# CHANGELOG

## [2.1.5](https://github.com/Bonislolz/dictrack/compare/2.1.4...2.1.5) - 2025-08-06
### Added
### Changed
### Fixed
- fix: Return tracker as a single-item list for consistency ([#43](https://github.com/Bonislolz/dictrack/issues/43))

## [2.1.4](https://github.com/Bonislolz/dictrack/compare/2.1.3...2.1.4) - 2025-08-02
### Added
- feat: add KeyValueInList and related classes for list-based checks ([#40](https://github.com/Bonislolz/dictrack/issues/40))
### Changed
- feat: filter out None values during tracker deserialization process ([#41](https://github.com/Bonislolz/dictrack/issues/41))
### Fixed

## [2.1.3](https://github.com/Bonislolz/dictrack/compare/2.1.2...2.1.3) - 2025-05-19
### Added
- feat: validate count limits and improve reset logic for limiters ([#38](https://github.com/Bonislolz/dictrack/issues/38))
### Changed
### Fixed

## [2.1.2](https://github.com/Bonislolz/dictrack/compare/2.1.1...2.1.2) - 2025-05-14
### Added
### Changed
### Fixed
- fix: python 2 syntax issue ([#36](https://github.com/Bonislolz/dictrack/issues/36))

## [2.1.1](https://github.com/Bonislolz/dictrack/compare/2.1.0...2.1.1) - 2025-05-09
### Added
### Changed
- perf: enhance `CountLimiter` `__repr__` output ([#34](https://github.com/Bonislolz/dictrack/issues/34))
### Fixed
- fix: correct reset logic and parameter handling ([#33](https://github.com/Bonislolz/dictrack/issues/33))

## [2.1.0](https://github.com/Bonislolz/dictrack/compare/2.0.10...2.1.0) - 2025-05-08
### Added
### Changed
### Fixed
- Improve reset flow ([#31](https://github.com/Bonislolz/dictrack/issues/31))

## [2.0.10](https://github.com/Bonislolz/dictrack/compare/2.0.9...2.0.10) - 2025-02-17
### Added
### Changed
### Fixed
- Fixed tuple nesting issue in type validation ([#29](https://github.com/Bonislolz/dictrack/issues/29))

## [2.0.9](https://github.com/Bonislolz/dictrack/compare/2.0.8...2.0.9) - 2025-02-13
### Added
### Changed
### Fixed
- Fixed stale data check failure in Python 3 ([#27](https://github.com/Bonislolz/dictrack/issues/27))

## [2.0.8](https://github.com/Bonislolz/dictrack/compare/2.0.7...2.0.8) - 2025-02-11
### Added
- Tracker now supports modifying progress ([#25](https://github.com/Bonislolz/dictrack/issues/25))
### Changed
### Fixed

## [2.0.7](https://github.com/Bonislolz/dictrack/compare/2.0.6...2.0.7) - 2025-01-20
### Added
- Tracker now support adding new targets ([#23](https://github.com/Bonislolz/dictrack/issues/23))
### Changed
### Fixed

## [2.0.6](https://github.com/Bonislolz/dictrack/compare/2.0.5...2.0.6) - 2025-01-08
### Added
### Changed
### Fixed
- Fixed misuse of `timedelta.seconds` in `TimeLimiter` ([#21](https://github.com/Bonislolz/dictrack/issues/21))

## YANKED [2.0.5](https://github.com/Bonislolz/dictrack/compare/2.0.4...2.0.5) - 2025-01-06
>  `TimeLimiter` component does not function as expected
### Added
### Changed
- Enhanced compatibility with older `redis-py` versions ([#19](https://github.com/Bonislolz/dictrack/issues/19))
### Fixed
- Fixed misuse of `timedelta.seconds` in `TimeLimiter` ([#17](https://github.com/Bonislolz/dictrack/issues/17))

## YANKED [2.0.4](https://github.com/Bonislolz/dictrack/compare/2.0.3...2.0.4) - 2024-12-14
>  `TimeLimiter` component does not function as expected
### Added
### Changed
- Modified `pymongo` version restriction from >=4.10.1 to >=3.0 in Python3.7+
### Fixed

## YANKED [2.0.3](https://github.com/Bonislolz/dictrack/compare/2.0.2...2.0.3) - 2024-12-14
>  `TimeLimiter` component does not function as expected
### Added
- Added new condition components:
  - `KeyValueContained`
  - `KeyValueNotContained`
  - `KeyNotExists`
  - `KeyValueNE`
- Added `pytest` unit test code for conditions and limiters
### Changed
- Modified `pre_track()` and `post_track()` param name, from `pre_track`/`post_track` to
`pre_tracker`/`post_tracker` in `CountLimiter` and `TimeLimiter`.
### Fixed
- Fixed `CountLimiter` that `limited` did not work correctly
  
## YANKED [2.0.2](https://github.com/Bonislolz/dictrack/compare/2.0.1...2.0.2) - 2024-11-19
>  `TimeLimiter` component does not function as expected
### Added
### Changed
### Fixed
- Fixed `MongoDBDataStore` flush process, using `delete_many()` instead of `drop()`
  
## YANKED [2.0.1](https://github.com/Bonislolz/dictrack/compare/2.0.0...2.0.1) - 2024-11-14
>  `TimeLimiter` component does not function as expected
### Added
- Added new parameter `strict` that performs strict type for data cache and data store.
### Changed
### Fixed


## YANKED [2.0.0](https://github.com/Bonislolz/dictrack/compare/1.1.0...2.0.0) - 2024-11-08
>  `TimeLimiter` component does not function as expected
#### BRAND NEW data system, adding data cache & data store, data cache for tracking, data store for permanently storing
#### BRAND NEW limiter component
### Added
- Added data cache components
  - `RedisDataCache`
  - `MemoryDataCache`
- Added data store component
  - `MongoDBDataStore`
- Added limiter components
  - `CountLimiter`
  - `TimeLimiter`
- Tracker now support multi-targets and loop forever mode
- Added new event `LIMITED`/`STAGE_COMPLETED`/`ALL_COMPLETED`
### Changed
### Fixed

## [1.1.0](https://github.com/Bonislolz/dictrack/compare/1.0.0...1.1.0) - 2024-10-27
### Added
- Added [MIT License](https://github.com/Bonislolz/dictrack?tab=MIT-1-ov-file)
### Changed
### Fixed
- Fixed `RedisDataStore` not working caused from missing pipeline execution

## REMOVED 1.0.3 - 2024-10-27
### Added
### Changed
### Fixed

## YANKED 1.0.2 - 2024-10-26
> RedisDataStore component does not function as expected
### Added
### Changed
### Fixed

## YANKED 1.0.1 - 2024-10-24
> Build failure for Python 2.7
### Added
### Changed
### Fixed

## REMOVED [1.0.0](https://github.com/Bonislolz/dictrack/tree/1.0.0) - 2024-10-24
#### HELLO WORLD
### Added
### Changed
### Fixed
