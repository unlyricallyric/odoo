# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.18] - 2022-06-13

### Added
- Added boolean field to connect with or without API key

## [1.1.17] - 2021-10-29

### Fixed
- Import product description


## [1.1.16] - 2021-05-24

### Added
- Sync Shipment Done


## [1.1.15] - 2021-05-24

### Added
- Sync Refund added


## [1.1.14] - 2021-04-21

### Changed
- Cron import objects with configured updated_at_min


## [1.1.13] - 2020-12-20

### Fixed
- 'multi.channel.skeleton' model type


## [1.1.11] - 2020-10-06

### Changed
- Not import refunded orders


## [1.1.10] - 2020-09-30

### Changed
- Address matching on order evaluation


## [1.1.9] - 2020-09-25

### Changed
- Imported datetime string in order


## [1.1.8] - 2020-09-24

### Changed
- Address matching on order evaluation


## [1.1.6-1.1.7] - 2020-09-23

### Changed
- Customer addresses to be imported as invoice type to keep address field data


## [1.1.5] - 2020-09-23

### Fixed
- Remove html tags from product description.


## [1.1.4] - 2020-09-11

### Added
- Mark order paid on shopify


## [1.1.2] - 2020-09-07

### Fixed
- GET product before PUT product due to ShopifyApi=8.0.0


## [1.1.1] - 2020-09-04

### Changed
- API version due to Cursor based pagination
- ShopifyApi lib version to 8.0.0

### Fixed
- Export Product due to change in shopify library.

### Removed
- adjust_quantity in favour of set_quantity


## [1.1.0] - 2020-09-04

### Added
- Cursor based pagination


## [1.0.8] - 2020-07-28

### Fixed
- Customer without name


## [1.0.7] - 2020-06-20

### Fixed
- Duplicate order.line.feed when import order again
