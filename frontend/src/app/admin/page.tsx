import TriggerPanel from "@/components/home/TriggerPanel";

export default function AdminPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">系统管理</h1>
        <p className="text-sm text-gray-500 mt-1">手动触发数据抓取与分析流程</p>
      </div>
      <TriggerPanel />
    </div>
  );
}
