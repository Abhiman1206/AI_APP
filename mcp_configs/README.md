# MCP Servers Setup Guide

This directory contains configuration files and setup instructions for Docling MCP and PaddleOCR MCP servers.

## Prerequisites

- Python 3.10+ (Python 3.14.3 is installed)
- `uv` package manager (installed)
- Internet connection for downloading dependencies

## Installed MCP Servers

### 1. Docling MCP Server

**Status:** ✅ Installed and ready to use

Docling MCP provides document conversion, generation, and manipulation capabilities.

**Installation Command:**
```bash
uvx --from docling-mcp docling-mcp-server --help
```

**Available Tools:**
- `conversion` - Convert documents between formats
- `generation` - Generate documents
- `manipulation` - Manipulate document content
- `llama-index-rag` - RAG using LlamaIndex
- `llama-stack-rag` - RAG using LlamaStack
- `llama-stack-ie` - Information extraction using LlamaStack

**Transport Options:**
- `stdio` - For Claude Desktop and LM Studio
- `sse` - For Llama Stack
- `streamable-http` - For container setups

**Test Command:**
```bash
uvx --from docling-mcp docling-mcp-server --transport stdio
```

---

### 2. PaddleOCR MCP Server

**Status:** ✅ Installed and ready to use

PaddleOCR MCP provides OCR (Optical Character Recognition) and document analysis capabilities.

**Installation Command:**
```bash
pip install paddleocr-mcp
```

**Available Pipelines:**
- `OCR` - Text detection and recognition
- `PP-StructureV3` - Layout analysis with markdown output
- `PaddleOCR-VL` - VLM-based layout extraction
- `PaddleOCR-VL-1.5` - Improved speed and accuracy

**Available Sources:**
- `aistudio` - Use PaddleOCR official service (requires API token)
- `qianfan` - Use Qianfan platform service (requires API key)
- `self_hosted` - Use your own hosted server
- `local` - Use local library (requires PaddlePaddle, not available for Python 3.14 on Windows)

**Test Command:**
```bash
paddleocr_mcp --help
```

---

## Configuration Files

The following configuration files are available in this directory:

### For Claude Desktop

1. **`claude_desktop_config_docling.json`** - Docling MCP only
2. **`claude_desktop_config_paddleocr_aistudio.json`** - PaddleOCR with AI Studio service
3. **`claude_desktop_config_paddleocr_selfhosted.json`** - PaddleOCR with self-hosted server
4. **`claude_desktop_config_paddleocr_qianfan.json`** - PaddleOCR with Qianfan service
5. **`claude_desktop_config_both.json`** - Both Docling and PaddleOCR (recommended)

### Claude Desktop Config Location

The Claude Desktop configuration file should be placed at:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
  - Full path: `C:\Users\<YourUsername>\AppData\Roaming\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

---

## Setup Instructions

### Option 1: Using Both MCPs (Recommended)

1. Copy the contents of `claude_desktop_config_both.json`
2. Create or edit `%APPDATA%\Claude\claude_desktop_config.json`
3. Replace `<your-server-url>` and `<your-access-token>` with your credentials
4. Restart Claude Desktop

### Option 2: Using Docling Only

1. Copy the contents of `claude_desktop_config_docling.json`
2. Create or edit `%APPDATA%\Claude\claude_desktop_config.json`
3. Restart Claude Desktop

### Option 3: Using PaddleOCR with Different Services

Choose one of the PaddleOCR config files based on your service:

- **AI Studio Service:** Use `claude_desktop_config_paddleocr_aistudio.json`
  - Get credentials from: https://aistudio.baidu.com/

- **Self-Hosted Server:** Use `claude_desktop_config_paddleocr_selfhosted.json`
  - Deploy your own PaddleOCR server following PaddleOCR serving docs

- **Qianfan Platform:** Use `claude_desktop_config_paddleocr_qianfan.json`
  - Get API key from: https://qianfan.baidubce.com/

---

## Using with uvx (Alternative Method)

Both MCPs can be run directly using uvx without permanent installation:

### Docling MCP
```bash
uvx --from docling-mcp docling-mcp-server --transport stdio
```

### PaddleOCR MCP (Self-Hosted)
```bash
uvx --from paddleocr-mcp paddleocr_mcp --pipeline OCR --ppocr_source self_hosted --server_url http://your-server-url
```

### Configuration for uvx in Claude Desktop

For Docling (already included in the configs):
```json
{
  "command": "uvx",
  "args": ["--from", "docling-mcp", "docling-mcp-server"]
}
```

For PaddleOCR:
```json
{
  "command": "uvx",
  "args": ["--from", "paddleocr-mcp", "paddleocr_mcp"]
}
```

---

## Testing the MCPs

### Test Docling MCP
```bash
# Show help
uvx --from docling-mcp docling-mcp-server --help

# Run with stdio transport
uvx --from docling-mcp docling-mcp-server --transport stdio
```

### Test PaddleOCR MCP
```bash
# Show help
paddleocr_mcp --help

# Test with verbose logging (requires service URL)
paddleocr_mcp --pipeline OCR --ppocr_source self_hosted --server_url http://127.0.0.1:8080 --verbose
```

---

## Troubleshooting

### Issue: PaddleOCR local mode not working
**Solution:** Local mode requires PaddlePaddle which is not available for Python 3.14 on Windows. Use one of the service-based modes (aistudio, qianfan, or self_hosted) instead.

### Issue: Claude Desktop doesn't show MCPs
**Solutions:**
1. Verify the config file is in the correct location
2. Check JSON syntax is valid
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

### Issue: MCP server fails to start
**Solutions:**
1. Test the command manually in terminal
2. Check all required credentials are provided
3. Verify network connectivity for service-based modes
4. Check environment variables are set correctly

---

## Advanced Configuration

### PaddleOCR Pipeline Optimization

For better performance, you can customize the pipeline configuration:

1. Create a custom config file with optimized settings
2. Set `PADDLEOCR_MCP_PIPELINE_CONFIG` to the config file path

Example for using mobile models (faster, less memory):
- Detection: `PP-OCRv5_mobile_det`
- Recognition: `PP-OCRv5_mobile_rec`

### Docling Toolgroups

You can specify which toolgroups to load:

```json
{
  "command": "uvx",
  "args": [
    "--from=docling-mcp",
    "docling-mcp-server",
    "conversion:generation:manipulation"
  ]
}
```

Available toolgroups:
- `conversion` (default)
- `generation` (default)
- `manipulation` (default)
- `llama-index-rag`
- `llama-stack-rag`
- `llama-stack-ie`

---

## Additional Resources

### Docling MCP
- GitHub: https://github.com/docling-project/docling-mcp.git
- Documentation: Check repository README

### PaddleOCR MCP
- GitHub: https://github.com/PaddlePaddle/PaddleOCR.git
- MCP Documentation: Check repository docs/version3.x/deployment/mcp_server.en.md
- Official Website: https://www.paddleocr.ai/

### MCP Protocol
- Specification: https://spec.modelcontextprotocol.io/

---

## Quick Start Commands

```bash
# Install both MCPs (already done)
pip install uv
pip install paddleocr-mcp

# Test Docling
uvx --from docling-mcp docling-mcp-server --help

# Test PaddleOCR
paddleocr_mcp --help

# Configure Claude Desktop
# 1. Edit %APPDATA%\Claude\claude_desktop_config.json
# 2. Use one of the config files in this directory
# 3. Add your credentials where needed
# 4. Restart Claude Desktop
```

---

## Environment Variables Reference

### PaddleOCR MCP

| Variable | CLI Argument | Type | Default | Description |
|----------|-------------|------|---------|-------------|
| `PADDLEOCR_MCP_PIPELINE` | `--pipeline` | str | `"OCR"` | Pipeline name |
| `PADDLEOCR_MCP_PPOCR_SOURCE` | `--ppocr_source` | str | `"local"` | Source type |
| `PADDLEOCR_MCP_SERVER_URL` | `--server_url` | str | `None` | Server base URL |
| `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN` | `--aistudio_access_token` | str | `None` | AI Studio token |
| `PADDLEOCR_MCP_QIANFAN_API_KEY` | `--qianfan_api_key` | str | `None` | Qianfan API key |
| `PADDLEOCR_MCP_TIMEOUT` | `--timeout` | int | `60` | HTTP timeout |
| `PADDLEOCR_MCP_DEVICE` | `--device` | str | `None` | Device for inference |
| `PADDLEOCR_MCP_PIPELINE_CONFIG` | `--pipeline_config` | str | `None` | Config file path |

---

## Notes

- Both MCP servers are successfully installed and ready to use
- Docling MCP works out of the box with uvx
- PaddleOCR MCP requires service credentials or a self-hosted server for your Python version
- All configuration files are ready in the `mcp_configs` directory
- Choose the configuration that matches your use case and available services

---

**Setup Date:** March 15, 2026
**Python Version:** 3.14.3
**Platform:** Windows 11
