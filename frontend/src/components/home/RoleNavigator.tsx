"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getRoles, type Role } from "@/lib/api";

const FALLBACK_ROLES: Role[] = [
  {
    key: "programmer", name: "程序员", icon: "💻",
    description: "自动化需求多、付费能力强、社区活跃",
    subtopics: ["Claude Code", "Cursor", "GitHub", "CI/CD", "MCP", "Agent"],
    demand_count: 0, avg_opportunity_score: 0,
  },
  {
    key: "content_creator", name: "自媒体创作者", icon: "📱",
    description: "内容生产压力大、高频工具需求、传播效率高",
    subtopics: ["小红书运营", "抖音创作", "视频剪辑", "选题策划"],
    demand_count: 0, avg_opportunity_score: 0,
  },
  {
    key: "teacher", name: "教师", icon: "📚",
    description: "行政工作繁重、重复表格多、AI 切入空间大",
    subtopics: ["备课", "教案", "课件制作", "班主任管理", "表格处理"],
    demand_count: 0, avg_opportunity_score: 0,
  },
  {
    key: "hr", name: "HR", icon: "👥",
    description: "简历筛选、面试安排等重复任务多",
    subtopics: ["简历筛选", "面试安排", "考勤管理", "薪酬计算"],
    demand_count: 0, avg_opportunity_score: 0,
  },
  {
    key: "lawyer", name: "律师", icon: "⚖️",
    description: "文书工作量大、格式要求高、付费意愿强",
    subtopics: ["合同审核", "文书生成", "案例检索"],
    demand_count: 0, avg_opportunity_score: 0,
  },
  {
    key: "cross_border_seller", name: "跨境卖家", icon: "🌐",
    description: "多平台数据管理、选品库存客服痛点突出",
    subtopics: ["选品分析", "库存管理", "客服自动化", "数据分析"],
    demand_count: 0, avg_opportunity_score: 0,
  },
];

export default function RoleNavigator() {
  const [roles, setRoles] = useState<Role[]>(FALLBACK_ROLES);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRoles().then((res) => {
      if (res.success && res.data && res.data.length > 0) {
        setRoles(res.data);
      }
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-6 w-48 rounded bg-gray-200 animate-pulse" />
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-32 rounded-xl bg-gray-100 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-900 mb-1">
        你想研究哪类人？
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        选择一个职业角色，发现该群体最迫切的需求
      </p>
      <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {roles.map((role) => (
          <Link
            key={role.key}
            href={`/roles/${role.key}`}
            className="group rounded-xl border border-gray-200 bg-white p-4 hover:border-indigo-300 hover:shadow-md transition-all"
          >
            <div className="text-2xl mb-2">{role.icon}</div>
            <h3 className="font-semibold text-gray-900 text-sm group-hover:text-indigo-700 transition-colors">
              {role.name}
            </h3>
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">
              {role.description}
            </p>
            {role.demand_count > 0 && (
              <div className="mt-2 flex items-center gap-2 text-xs text-gray-400">
                <span>{role.demand_count} 个需求</span>
                {role.avg_opportunity_score > 0 && (
                  <span className="text-amber-600 font-medium">
                    {role.avg_opportunity_score.toFixed(0)} 分
                  </span>
                )}
              </div>
            )}
          </Link>
        ))}
      </div>
    </section>
  );
}
