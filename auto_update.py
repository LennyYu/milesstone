"""
自动更新总指挥脚本 - 一键完成：数据更新 -> 模型预测 -> 生成报告 -> 推送GitHub
放置位置：pythonProject/ 目录下（仓库根目录的外面）
运行方式：python auto_update.py
"""
import os
import sys
import subprocess
import datetime
import shutil

# ===== 路径配置（请根据实际情况修改） =====
PROJECT_ROOT = "F:/MileStone/二级量化/THS/pythonProject"
REPO_ROOT = os.path.join(PROJECT_ROOT, "milesstone")

# 各脚本路径
MINUTE_UPDATE_SCRIPT = os.path.join(PROJECT_ROOT, "上证指数分钟行情自动更新.py")
DAILY_UPDATE_SCRIPT = os.path.join(PROJECT_ROOT, "上证指数日线行情自动更新脚本.py")
XGB_SCRIPT = os.path.join(PROJECT_ROOT, "XGBoost简单预测初应用.py")
REPORT_GENERATOR = os.path.join(REPO_ROOT, "report_generator.py")

# 日志路径
LOG_FILE = os.path.join(PROJECT_ROOT, "auto_update.log")


def log(msg, level="INFO"):
    """打印并记录日志"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[{}] [{}] {}".format(timestamp, level, msg)
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_script(script_path, cwd=None, env_extra=None):
    """运行一个Python脚本，返回(returncode, stdout, stderr)"""
    if not os.path.exists(script_path):
        log("脚本不存在: {}".format(script_path), "WARNING")
        return 1, "", "脚本文件不存在"

    log("执行脚本: {}".format(os.path.basename(script_path)))

    # 设置matplotlib后端为Agg（避免弹窗卡住）
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    if env_extra:
        env.update(env_extra)

    result = subprocess.run(
        [sys.executable, script_path],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=300  # 5分钟超时
    )

    if result.stdout:
        log("STDOUT: {}".format(result.stdout.strip()[:500]))
    if result.stderr:
        log("STDERR: {}".format(result.stderr.strip()[:500]), "WARNING")

    return result.returncode, result.stdout, result.stderr


def git_operation(cmd, cwd):
    """执行git命令"""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60
    )
    return result.returncode, result.stdout, result.stderr


# ===== 主流程 =====
def main():
    log("=" * 60)
    log("自动更新流程启动")
    log("当前时间: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    log("=" * 60)

    # 检查仓库是否存在
    if not os.path.exists(REPO_ROOT):
        log("错误: 仓库目录不存在: {}".format(REPO_ROOT), "ERROR")
        log("请确认 milesstone 文件夹已正确克隆到: {}".format(REPO_ROOT))
        sys.exit(1)

    # 检查必要文件
    missing = []
    if not os.path.exists(DAILY_UPDATE_SCRIPT):
        missing.append("上证指数日线行情自动更新脚本.py")
    if not os.path.exists(XGB_SCRIPT):
        missing.append("XGBoost简单预测初应用.py")
    if not os.path.exists(REPORT_GENERATOR):
        missing.append("report_generator.py")

    if missing:
        log("警告: 以下文件不存在，部分步骤将被跳过: {}".format(", ".join(missing)))

    # ===== 步骤1: 更新分钟行情数据 =====
    log("\n" + "=" * 40)
    log("[1/5] 更新分钟行情数据")
    log("=" * 40)
    if os.path.exists(MINUTE_UPDATE_SCRIPT):
        rc, out, err = run_script(MINUTE_UPDATE_SCRIPT)
        if rc == 0:
            log("分钟数据更新成功", "OK")
        else:
            log("分钟数据更新失败 (code={})".format(rc), "ERROR")
            # 不中断流程，继续执行
    else:
        log("跳过: 分钟更新脚本不存在", "WARNING")

    # ===== 步骤2: 更新日线行情数据 =====
    log("\n" + "=" * 40)
    log("[2/5] 更新日线行情数据")
    log("=" * 40)
    if os.path.exists(DAILY_UPDATE_SCRIPT):
        rc, out, err = run_script(DAILY_UPDATE_SCRIPT)
        if rc == 0:
            log("日线数据更新成功", "OK")
        else:
            log("日线数据更新失败 (code={})".format(rc), "ERROR")
            log("请检查iFinD连接和数据脚本", "ERROR")
            sys.exit(1)
    else:
        log("错误: 日线更新脚本不存在，无法继续", "ERROR")
        sys.exit(1)

    # ===== 步骤3: 运行XGBoost预测 =====
    log("\n" + "=" * 40)
    log("[3/5] 运行XGBoost预测模型")
    log("=" * 40)
    if os.path.exists(XGB_SCRIPT):
        rc, out, err = run_script(XGB_SCRIPT)
        if rc == 0:
            log("XGBoost预测完成", "OK")
            # 检查CSV是否生成
            csv_path = os.path.join(PROJECT_ROOT, "行情数据", "预测结果_近期.csv")
            if os.path.exists(csv_path):
                log("预测结果CSV已生成: {}".format(csv_path))
            else:
                log("警告: 预测结果CSV未找到", "WARNING")
        else:
            log("XGBoost预测失败 (code={})".format(rc), "ERROR")
            log("请检查XGBoost脚本是否有错误", "ERROR")
            sys.exit(1)
    else:
        log("错误: XGBoost脚本不存在，无法继续", "ERROR")
        sys.exit(1)

    # ===== 步骤4: 生成HTML报告 =====
    log("\n" + "=" * 40)
    log("[4/5] 生成HTML报告")
    log("=" * 40)
    if os.path.exists(REPORT_GENERATOR):
        rc, out, err = run_script(REPORT_GENERATOR, cwd=REPO_ROOT)
        if rc == 0:
            log("HTML报告生成成功", "OK")
            # 验证文件
            html_path = os.path.join(REPO_ROOT, "docs", "index.html")
            if os.path.exists(html_path):
                log("index.html 已生成: {}".format(html_path))
            else:
                log("警告: index.html 未找到", "WARNING")
        else:
            log("HTML报告生成失败 (code={})".format(rc), "ERROR")
            sys.exit(1)
    else:
        log("错误: report_generator.py 不存在，无法继续", "ERROR")
        sys.exit(1)

    # ===== 步骤5: 推送到GitHub =====
    log("\n" + "=" * 40)
    log("[5/5] 推送到GitHub")
    log("=" * 40)

    # git add
    rc, out, err = git_operation(["git", "add", "docs/index.html"], REPO_ROOT)
    if rc != 0:
        log("git add 失败: {}".format(err), "ERROR")
        sys.exit(1)

    # git commit
    commit_msg = "update: {} 择时报告自动更新".format(datetime.date.today())
    rc, out, err = git_operation(["git", "commit", "-m", commit_msg], REPO_ROOT)
    if rc != 0:
        # 如果没有变化，git commit会返回非0，这不算错误
        if "nothing to commit" in err or "nothing added" in err:
            log("没有需要提交的更改（文件可能未变动）", "WARNING")
        else:
            log("git commit 失败: {}".format(err), "ERROR")
            sys.exit(1)
    else:
        log("git commit 成功", "OK")

        # git push
        rc, out, err = git_operation(["git", "push"], REPO_ROOT)
        if rc == 0:
            log("git push 成功!", "OK")
        else:
            log("git push 失败: {}".format(err), "ERROR")
            log("请检查Git凭证配置", "ERROR")
            sys.exit(1)

    # ===== 完成 =====
    log("\n" + "=" * 60)
    log("自动更新流程全部完成!")
    log("网页链接: https://lennyyu.github.io/milesstone/")
    log("=" * 60)


if __name__ == "__main__":
    main()
