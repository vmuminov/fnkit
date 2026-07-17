# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-07-18

### Added

- `as_result` function wrapper, transforming ordinary functions a -> b into a -> Result b e, where e is Exception
- Collection type as a thin wrapper around python's iterators

### Changed

- Result and Option protocols are now `@runtime_checkable`

## [0.5.0] - 2026-07-17

### Added

- Option, Result, State types
- Transformers for State(Option) and State(Result)
