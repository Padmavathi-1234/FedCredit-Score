/**
 * Dashboard.js — Results dashboard logic
 * Handles score animation, Chart.js pie chart,
 * 5Cs display, explanations, and report download.
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('dashboardApp', () => ({
        result: null,
        displayScore: 0,
        scoreAnimated: false,

        init() {
            const stored = sessionStorage.getItem('analysisResult');
            if (!stored) {
                window.location.href = '/';
                return;
            }

            this.result = JSON.parse(stored);

            this.$nextTick(() => {
                this.animateScore();
                this.initChart();
            });
        },

        // Score
        get score() {
            return this.result?.scoring?.federated_score ?? 0;
        },

        get riskCategory() {
            return this.result?.scoring?.risk_category ?? 'N/A';
        },

        get riskClass() {
            const cat = this.riskCategory.toLowerCase();
            if (cat.includes('low')) return 'low';
            if (cat.includes('medium')) return 'medium';
            return 'high';
        },

        get scoreClass() {
            const cat = this.riskCategory.toLowerCase();
            if (cat.includes('medium')) return 'medium';
            if (cat.includes('high')) return 'high-risk';
            return '';
        },

        // Loan
        get loan() {
            return this.result?.scoring?.loan_recommendation ?? {};
        },

        // Bank scores
        get bankScores() {
            return this.result?.scoring?.bank_scores ?? [];
        },

        // Intelligence
        get intelligence() {
            return this.result?.intelligence ?? {};
        },

        // Financial data
        get financial() {
            return this.result?.financial_data ?? {};
        },

        // Risk breakdown
        get breakdown() {
            return this.result?.scoring?.risk_breakdown ?? {};
        },

        // 5Cs
        get fiveCs() {
            return this.result?.scoring?.five_cs ?? [];
        },

        // Risk narrative
        get riskNarrative() {
            return this.result?.scoring?.risk_narrative ?? 'Risk narrative not available.';
        },

        // ── Explanation generators ──
        getRiskExplanation() {
            const s = this.score;
            const cat = this.riskCategory;
            if (s >= 700) {
                return `A score of ${s}/1000 indicates strong creditworthiness. The company demonstrates solid financial health, regulatory compliance, and positive market signals. Lenders can extend credit with high confidence at competitive rates.`;
            } else if (s >= 400) {
                return `A score of ${s}/1000 reflects moderate creditworthiness. The company has acceptable fundamentals but shows areas that need improvement. Lenders may proceed with standard risk provisioning and monitoring.`;
            } else {
                return `A score of ${s}/1000 signals significant credit risk. Multiple indicators — including financial health, compliance, or market conditions — raise concerns. Detailed due diligence is strongly recommended before lending.`;
            }
        },

        getFinancialSummary() {
            const f = this.financial;
            const parts = [];

            if (f.turnover) {
                const t = typeof f.turnover === 'number' ? '₹' + f.turnover.toLocaleString('en-IN') : f.turnover;
                parts.push(`Revenue stands at ${t}`);
            }
            if (f.profit_margin) {
                const pm = typeof f.profit_margin === 'number' ? (f.profit_margin * 100).toFixed(1) + '%' : f.profit_margin;
                parts.push(`with a profit margin of ${pm}`);
            }
            if (f.debt_ratio) {
                const dr = typeof f.debt_ratio === 'number' ? f.debt_ratio.toFixed(2) : f.debt_ratio;
                const level = f.debt_ratio <= 0.4 ? 'conservative' : f.debt_ratio <= 0.6 ? 'moderate' : 'elevated';
                parts.push(`The debt ratio of ${dr} indicates ${level} leverage`);
            }
            if (f.capacity_utilization) {
                parts.push(`Capacity utilization is at ${f.capacity_utilization}`);
            }

            if (parts.length === 0) return 'Financial metrics were not fully extracted from the uploaded documents.';
            return parts.join('. ') + '. These metrics directly feed into the Capacity and Capital dimensions of the 5Cs assessment.';
        },

        // ── Score Counter Animation ──
        animateScore() {
            const target = this.score;
            const duration = 2000;
            const start = performance.now();

            const step = (now) => {
                const elapsed = now - start;
                const progress = Math.min(elapsed / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                this.displayScore = Math.round(eased * target);

                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                    this.scoreAnimated = true;
                }
            };

            requestAnimationFrame(step);
        },

        // ── Chart.js ──
        initChart() {
            const ctx = document.getElementById('riskChart');
            if (!ctx || typeof Chart === 'undefined') return;

            const labels = Object.keys(this.breakdown);
            const data = Object.values(this.breakdown);

            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{
                        data,
                        backgroundColor: [
                            '#6366f1',
                            '#22d3ee',
                            '#f59e0b',
                            '#10b981',
                        ],
                        borderColor: 'rgba(15, 15, 46, 0.9)',
                        borderWidth: 3,
                        hoverOffset: 8,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    cutout: '60%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#94a3b8',
                                font: {
                                    family: "'Inter', sans-serif",
                                    size: 12,
                                },
                                padding: 16,
                                usePointStyle: true,
                                pointStyleWidth: 12,
                            },
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 15, 46, 0.95)',
                            titleColor: '#f1f5f9',
                            bodyColor: '#94a3b8',
                            borderColor: 'rgba(99, 102, 241, 0.3)',
                            borderWidth: 1,
                            cornerRadius: 8,
                            padding: 12,
                            callbacks: {
                                label: (ctx) => `${ctx.label}: ${ctx.parsed}%`,
                            },
                        },
                    },
                    animation: {
                        animateRotate: true,
                        duration: 1500,
                    },
                },
            });
        },

        // ── Report Download ──
        async downloadReport() {
            const id = this.result?.analysis_id;
            if (!id) return;

            try {
                const response = await fetch(`/api/report/${id}`);
                if (!response.ok) throw new Error('Failed to generate report');

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `FedCredit_Report_${id.substring(0, 8)}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
            } catch (err) {
                alert('Report download failed: ' + err.message);
            }
        },

        // ── Helpers ──
        formatCurrency(val) {
            if (typeof val !== 'number') return String(val);
            return '₹' + val.toLocaleString('en-IN');
        },

        formatPercent(val) {
            if (typeof val !== 'number') return String(val);
            return (val * 100).toFixed(1) + '%';
        },
    }));
});
