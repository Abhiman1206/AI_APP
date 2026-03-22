# MCP Servers - Quick Reference

## Setup Status: ✅ COMPLETED

Both Docling MCP and PaddleOCR MCP servers are successfully installed and configured.

---

## Installed Software

1. **uv/uvx** - Package manager (version 0.10.10)
2. **Docling MCP Server** - Document processing capabilities
3. **PaddleOCR MCP Server** - OCR and document analysis capabilities (version 0.5.0)

---

## Quick Test Commands

### Test Docling MCP
```bash
uvx --from docling-mcp docling-mcp-server --help
```

### Test PaddleOCR MCP
```bash
paddleocr_mcp --help
```

---

## Configuration Files Location

All configuration files are in: `mcp_configs/`

Available configs:
1. `claude_desktop_config_docling.json` - Docling only
2. `claude_desktop_config_paddleocr_aistudio.json` - PaddleOCR with AI Studio
3. `claude_desktop_config_paddleocr_selfhosted.json` - PaddleOCR self-hosted
4. `claude_desktop_config_paddleocr_qianfan.json` - PaddleOCR with Qianfan
5. `claude_desktop_config_both.json` - Both MCPs (recommended)

---

## Next Steps

### To Use with Claude Desktop:

1. **Locate Claude Desktop config:**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Full path: `C:\Users\Asus\AppData\Roaming\Claude\claude_desktop_config.json`

2. **Choose your config:**
   - For both MCPs: Use `mcp_configs/claude_desktop_config_both.json`
   - For Docling only: Use `mcp_configs/claude_desktop_config_docling.json`
   - For PaddleOCR: Choose based on your service

3. **Add credentials (if using PaddleOCR services):**
   - Replace `<your-server-url>` with actual server URL
   - Replace `<your-access-token>` or `<your-api-key>` with your credentials

4. **Restart Claude Desktop**

### To Use from Command Line:

#### Docling MCP
```bash
# Run with stdio transport (default)
uvx --from docling-mcp docling-mcp-server

# Run with HTTP transport
uvx --from docling-mcp docling-mcp-server --transport streamable-http --host 0.0.0.0 --port 8000

# Load specific toolgroups
uvx --from docling-mcp docling-mcp-server conversion:generation
```

#### PaddleOCR MCP
```bash
# With AI Studio service
PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN=your_token paddleocr_mcp --pipeline OCR --ppocr_source aistudio --server_url https://your-server.aistudio-hub.baidu.com

# With self-hosted server
paddleocr_mcp --pipeline OCR --ppocr_source self_hosted --server_url http://127.0.0.1:8080

# With HTTP transport for remote access
paddleocr_mcp --pipeline OCR --ppocr_source self_hosted --server_url http://127.0.0.1:8080 --http --host 0.0.0.0 --port 8000
```

---

## Docling MCP Capabilities

- **Document Conversion:** Convert between formats (PDF, DOCX, HTML, Markdown, etc.)
- **Document Generation:** Create new documents
- **Document Manipulation:** Edit and modify document content
- **RAG Integration:** LlamaIndex and LlamaStack support
- **Information Extraction:** Extract structured data from documents

**Default toolgroups:** conversion, generation, manipulation

---

## PaddleOCR MCP Capabilities

### Pipelines:
1. **OCR** - Basic text detection and recognition
2. **PP-StructureV3** - Layout analysis with markdown output
3. **PaddleOCR-VL** - Vision-Language Model based extraction
4. **PaddleOCR-VL-1.5** - Improved VL model (faster and more accurate)

### Sources:
- **aistudio** - Official PaddleOCR cloud service (requires token)
- **qianfan** - Baidu Qianfan platform (requires API key)
- **self_hosted** - Your own deployed server
- **local** - Local library (not available for Python 3.14 on Windows)

---

## Important Notes

1. **PaddleOCR Local Mode:** Not available for Python 3.14 on Windows due to PaddlePaddle compatibility. Use service-based modes instead.

2. **Credentials Required:** PaddleOCR service modes require:
   - AI Studio: Access token from https://aistudio.baidu.com/
   - Qianfan: API key from https://qianfan.baidubce.com/
   - Self-hosted: Your own server URL

3. **Performance:** For better performance with PaddleOCR:
   - Use mobile models for faster inference
   - Disable unused features in PP-StructureV3
   - Adjust timeout for large documents

4. **Transport Options:**
   - `stdio` - For Claude Desktop, LM Studio (default)
   - `sse` - For Llama Stack
   - `streamable-http` - For containers and remote access

---

## Troubleshooting

**Issue:** Command not found
**Solution:** Restart terminal or run: `source ~/.bashrc` (Linux/Mac) or open new terminal (Windows)

**Issue:** PaddleOCR local mode fails
**Solution:** Use service-based mode (aistudio, qianfan, or self_hosted)

**Issue:** Claude Desktop doesn't detect MCPs
**Solution:**
1. Check config file location and syntax
2. Verify credentials are correct
3. Restart Claude Desktop completely

---

## Documentation

Full documentation is available in `mcp_configs/README.md`

GitHub repositories:
- Docling MCP: https://github.com/docling-project/docling-mcp.git
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR.git

---

**Setup completed:** March 15, 2026
**System:** Windows 11, Python 3.14.3
