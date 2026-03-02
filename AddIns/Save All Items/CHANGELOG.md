# Changelog

All notable changes to the "Save All Items" Fusion 360 Add-In will be documented in this file.

## [1.0.0] - 2024-02-19

### Added
- Initial release of Save All Items add-in
- Bulk export functionality for components and bodies
- Support for 4 export formats: 3MF, STL (Binary), STL (ASCII), OBJ
- Selection preview table showing items to be exported
- File naming convention: `[BrowserName]_[ProjectName].[ext]`
- Mesh refinement options: Low, Medium, High
- Open folder when done option
- Error handling with detailed summary reporting
- Filename sanitization for cross-platform compatibility
- Support for mixed selections (components + bodies)
- Nested component flattening with name preservation (3MF)
- Command button in Utilities tab
- Comprehensive documentation (README, QUICKSTART, IMPLEMENTATION_NOTES)

### Technical Details
- Built on Fusion 360 Add-In scaffold
- Uses native Fusion 360 export APIs
- No external dependencies
- Cross-platform support (Windows/macOS)
- Debug logging support

### Known Issues
- None reported yet

---

## Future Releases

### Planned for 1.1.0
- [ ] Progress bar for large exports
- [ ] Export presets/configurations
- [ ] Material assignment export (OBJ/MTL)

### Potential Future Features
- [ ] Batch processing with saved selection sets
- [ ] Template-based filename patterns
- [ ] Runtime unit conversion
- [ ] Incremental export (only changed items)
- [ ] Background export queue
- [ ] Cloud storage integration
- [ ] Mesh validation and repair
- [ ] Export statistics and analytics
