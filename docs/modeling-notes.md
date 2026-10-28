# 建模说明

项目以 Blender 4.5.3 为主要制作环境，采用地图轮廓、程序化建筑、重点建筑手工细化、树木实例和标注数据组合生成。

## 目录约定

为了让历史脚本保持可运行，`src/outputs` 和 `src/work` 保留了原项目的相对位置关系：

- `src/outputs`：Blender Python 脚本、轮廓数据、标注数据和查看器模板。
- `src/work`：脚本运行时需要的地图文字块数据和查看器 bundle。

## 典型流程

1. 在 Blender 4.5.3 中准备基础场景。
2. 使用 `build_campus_v3.py` 生成或更新校园几何和材质。
3. 使用 `finalize_v3.py` 完成重点建筑、标注和静态视图。
4. 使用 `export_v3_viewer.py` 导出 GLB。
5. 使用 `validate_v3.py` 检查模型和导出结果。

完整的现成工程和导出结果请从 Release 获取；源码脚本主要用于复现和继续开发。

