import re

path = r"E:\Desktop\langchain-business-trip-management\docs\ARCHITECTURE_V2_PLAN.md"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Find P2 section by line number
lines = content.split("\n")
p2_line = None
for i, line in enumerate(lines):
    if "#### P2" in line:
        p2_line = i
        break

if p2_line is not None:
    print(f"P2 section at line {p2_line+1}: {repr(lines[p2_line][:60])}")
    
    # Update status: //u5f85/u542f/u52a8 -> (2026-07-13) /u2705 /u90e8/u5206/u5b8c/u6210
    old_status = "待启动"
    new_status = "(2026-07-13) \u2705 \u90e8\u5206\u5b8c\u6210"
    
    if old_status in lines[p2_line]:
        lines[p2_line] = lines[p2_line].replace(old_status, new_status)
        print("  Status line updated")
    
    # Update checkboxes in subsequent lines
    for j in range(p2_line+1, min(p2_line+10, len(lines))):
        # Check for items that should be [x]
        line = lines[j]
        if "- [ ] 旧代码清理" in line:
            lines[j] = line.replace("- [ ]", "- [x]")
            print(f"  Line {j+1}: deprecated marked")
        elif "- [ ] Grafana Dashboard" in line:
            lines[j] = line.replace("- [ ]", "- [x]")
            print(f"  Line {j+1}: grafana dashboard marked")
        elif "- [ ] AlertManager 飞书集成" in line:
            lines[j] = line.replace("- [ ]", "- [x]")
            print(f"  Line {j+1}: alertmanager marked")
        elif "- [ ] 全链路 LangSmith" in line:
            lines[j] = line.replace("- [ ]", "- [x]")
            print(f"  Line {j+1}: langsmith marked")
    
    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("P2 section updated successfully")
else:
    print("P2 section NOT FOUND")
    # DEBUG: search for 'P2' more broadly
    for i, line in enumerate(lines):
        if "P2" in line:
            print(f"  Line {i+1}: {line[:80]}")
