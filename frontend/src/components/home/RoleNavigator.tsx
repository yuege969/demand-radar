"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getRoles, type Role } from "@/lib/api";

const ROLE_ICONS: Record<string, React.ReactNode> = {
  programmer: (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L21 12l-3.75 5.25M6.75 17.25L3 12l3.75-5.25M14.25 3.75l-4.5 16.5" />
    </svg>
  ),
  content_creator: (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
    </svg>
  ),
  teacher: (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
    </svg>
  ),
  hr: (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
    </svg>
  ),
  lawyer: (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
    </svg>
  ),
  cross_border_seller: (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
    </svg>
  ),
};

const FALLBACK_ROLES: Role[] = [
  { key: "programmer", name: "程序员", icon: "", description: "自动化需求多、付费能力强、社区活跃", subtopics: ["Claude Code", "Cursor", "GitHub", "CI/CD", "MCP", "Agent"], demand_count: 0, avg_opportunity_score: 0 },
  { key: "content_creator", name: "自媒体创作者", icon: "", description: "内容生产压力大、高频工具需求、传播效率高", subtopics: ["小红书运营", "抖音创作", "视频剪辑", "选题策划"], demand_count: 0, avg_opportunity_score: 0 },
  { key: "teacher", name: "教师", icon: "", description: "行政工作繁重、重复表格多、AI 切入空间大", subtopics: ["备课", "教案", "课件制作", "班主任管理", "表格处理"], demand_count: 0, avg_opportunity_score: 0 },
  { key: "hr", name: "HR", icon: "", description: "简历筛选、面试安排等重复任务多", subtopics: ["简历筛选", "面试安排", "考勤管理", "薪酬计算"], demand_count: 0, avg_opportunity_score: 0 },
  { key: "lawyer", name: "律师", icon: "", description: "文书工作量大、格式要求高、付费意愿强", subtopics: ["合同审核", "文书生成", "案例检索"], demand_count: 0, avg_opportunity_score: 0 },
  { key: "cross_border_seller", name: "跨境卖家", icon: "", description: "多平台数据管理、选品库存客服痛点突出", subtopics: ["选品分析", "库存管理", "客服自动化", "数据分析"], demand_count: 0, avg_opportunity_score: 0 },
];

export default function RoleNavigator() {
  const [roles, setRoles] = useState<Role[]>(FALLBACK_ROLES);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRoles().then((res) => {
      if (res.success && res.data && res.data.length > 0) setRoles(res.data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <section className="space-y-3">
        <div className="h-5 w-40 rounded bg-surface-2 animate-pulse" />
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-28 rounded-[10px] bg-surface-1 animate-pulse" />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section>
      <h2 className="text-[15px] font-semibold text-text-primary mb-1">你想研究哪类人？</h2>
      <p className="text-[13px] text-text-secondary mb-4">选择一个职业角色，发现该群体最迫切的需求</p>
      <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {roles.map((role) => (
          <Link
            key={role.key}
            href={`/roles/${role.key}`}
            className="card-lift group rounded-[10px] border border-hairline bg-surface-1 p-4"
          >
            <div className="mb-2.5 text-accent opacity-80 group-hover:opacity-100 transition-opacity">
              {ROLE_ICONS[role.key] || ROLE_ICONS.programmer}
            </div>
            <h3 className="text-[14px] font-semibold text-text-primary group-hover:text-accent transition-colors">
              {role.name}
            </h3>
            <p className="text-[12px] text-text-muted mt-1 line-clamp-2 leading-relaxed">
              {role.description}
            </p>
            {role.demand_count > 0 && (
              <div className="mt-2.5 flex items-center gap-2 text-[11px] text-text-muted font-mono">
                <span>{role.demand_count} 个需求</span>
                {role.avg_opportunity_score > 0 && (
                  <span className="text-amber font-medium">{role.avg_opportunity_score.toFixed(0)} 分</span>
                )}
              </div>
            )}
          </Link>
        ))}
      </div>
    </section>
  );
}
