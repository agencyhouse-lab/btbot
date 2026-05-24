# 🐛 Known Bugs & Issues

## Bug #1: atbot.py - Integer Division Error
**Status**: 🔴 CRITICAL  
**Error**: `integer division or modulo by zero`  
**Location**: Trading loop  
**Impact**: Bot crashes every 30 seconds  
**Root Cause**: Likely dividing by zero in signal calculation or position sizing

**Stack Trace**:
