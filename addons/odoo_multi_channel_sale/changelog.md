# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2022-10-28

### Added
- Module is now supported to odoo version 16.0
- `description` field is introduced to the product feed to support the sync of product description.
- `wk_time_zone` field is introduced to channel configuration to fix issues in channel and odoo document date differences.
- Instance creation right from the kanban view of the instances.
- Direct record view button of Products, customers, categories & orders from the form view of the instance.
- Support update operation for mass export action via dashboard/instance export button.
### Fixed
- Order confirmation every time when the order feed is getting updated and evaluated.

## [2.3.14] - 2022-06-29

### Added
- `total_record_limit` field introduced to limit number of records to import in order to avoid timeout.
### Fixed
- Default product added for Delivery and Discount products.

## [2.3.13] - 2022-06-23

### Added
- `vat` field introduced in order and partner feed


## [2.3.13] - 2022-02-14

### Added
- `wk_default_code` field introduced for managing product template specific sku


## [2.3.12] - 2021-10-29

### Fixed
- Product Write


## [2.3.11] - 2021-05-28

### Fixed
- Default placeholder image render
## Added
- New alias image name controller


## [2.3.9] - 2021-04-07

### Fixed
- Instance Kanban View


## [2.3.8] - 2021-04-06

### Fixed
- Get Tax Ids from tax lines in order feed


## [2.3.7] - 2021-04-05

### Fixed
- Window Actions


## [2.3.6] - 2021-01-23

### Fixed
- Product/Partner/Order form view


## [2.3.5] - 2021-01-18

### Fixed
- Category & Product Feed view

## [2.3.4] - 2020-12-21

### Fixed
- Picking validation
- Feed contextualization


## [2.2.13] - 2020-09-25

### Changed
- demo.xml to data.xml
- Datetime format parsing

### Removed
- Feed sequence records from data.xml
- StockMove POS Order operation


## [2.2.12] - 2020-09-11

### Changed
- Stock move location checked with channel location and associated child locations

### Added
- Set need_sync to True, when pricelist_item is updated.


## [2.2.11] - 2020-09-08

### Added
- Unlink product variant mappings when unlinking product template mapping


## [2.2.10] - 2020-09-07

### Fixed
- Instance kanban view with large numbers
-
### Deprecated
- weight_unit in product.variant.feed


## [2.2.9] - 2020-09-01

### Fixed
- Variant feed write


## [2.2.8] - 2020-09-01

### Fixed
- Import Infinity loop when api_imit==1


## [2.2.7] - 2020-07-16

### Fixed
- Mapping button in feed form view


## [2.2.6] - 2020-07-15

### Fixed
- Dashboard name conflict with website
- Contextualized variant feed dictionary with template it


## [2.2.3] - 2020-07-10

### Changed
- Show parent partner record only in tree view
- Count parent partner record only in Customer count


## [2.2.2] - 2020-07-07

### Fixed
- Set invoice as 'paid' where state == 'posted'


## [2.2.1] - 2020-07-03

### Fixed
- Contextualized mapping with product_id


## [2.1.11] - 2020-06-23

### Fixed
- Duplicate order.line.feed when feed is updated.


## [2.1.10] - 2020-06-18

### Fixed
- On variant creation/updation, barcode unique error due to `barcode == ''`


## [2.1.9] - 2020-05-28

### Fixed
- In Instance Dashboard controller, month label obtained from db stripped.

