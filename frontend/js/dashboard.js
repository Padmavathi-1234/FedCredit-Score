/**
 * Dashboard.js — Results dashboard logic
 * Handles history fetching, session loading,
 * score animation, Chart.js pie chart,
 * 5Cs display, explanations, and report download.
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('dashboardApp', () => ({
        user: null,
        history: [],
        loadingHistory: true,
        loadingAnalysis: false,
        result: null,
        sessionMessages: [],
        currentSessionId: null,
        displayScore: 0,
        scoreAnimated: false,

        async init() {
            // No auth check required
            this.user = { name: "Guest User" };

            await this.fetchHistory();

            // Decide which session to load
            const loadLatest = sessionStorage.getItem('loadLatest');
            const urlParams = new URLSearchParams(window.location.search);
            const sessionId = urlParams.get('id');

            if (loadLatest === 'true' && this.history.length > 0) {
                sessionStorage.removeItem('loadLatest');
                await this.loadSession(this.history[0].id);
            } else if (sessionId) {
                await this.loadSession(sessionId);
            } else if (this.history.length > 0) {
                // optionally auto-load the first one
                await this.loadSession(this.history[0].id);
            }
        },

        async fetchHistory() {
            try {
                this.loadingHistory = true;
                const res = await fetch('/api/history');
                if (res.ok) {
                    this.history = await res.json();
                }

            } catch (err) {
                console.error("Failed to load history", err);
            } finally {
                this.loadingHistory = false;
            }
        },

        async loadSession(sessionId) {
            this.loadingAnalysis = true;
            this.currentSessionId = sessionId;
            this.result = null;
            this.sessionMessages = [];

            try {
                const res = await fetch(`/api/analysis/${sessionId}`);
                if (res.ok) {
                    const data = await res.json();
                    this.sessionMessages = data.messages || [];

                    // We extract the analysis_result message from data.messages
                    const resultMessage = data.messages.find(m => m.message_type === "analysis_result");

                    if (resultMessage) {
                        this.result = resultMessage.content;
                        // Replace url to reflect current ID
                        window.history.replaceState(null, "", `?id=${sessionId}`);

                        this.$nextTick(() => {
                            this.displayScore = 0;
                            this.scoreAnimated = false;
                            this.animateScore();
                            this.initChart();
                        });
                    } else {
                        throw new Error("Analysis results not ready or corrupted for this session.");
                    }
                }
            } catch (err) {
                console.error("Failed to load session", err);
                alert("Could not load this analysis session.");
            } finally {
                this.loadingAnalysis = false;
            }
        },

        async deleteSession(sessionId) {
            if (!confirm('Are you sure you want to delete this analysis permanently?')) return;
            try {
                const res = await fetch(`/api/analysis/${sessionId}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    this.history = this.history.filter(s => s.id !== sessionId);
                    if (this.currentSessionId === sessionId) {
                        this.result = null;
                        this.currentSessionId = null;
                        window.history.replaceState(null, "", `/dashboard`);
                    }
                }
            } catch (err) {
                alert("Failed to delete session: " + err.message);
            }
        },

        logout() {
            window.location.href = '/';
        },

        formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        },

        // --- Extracted existing getters & helpers ---

        get score() { return this.result?.scoring?.federated_score ?? 0; },
        get originalScore() { return this.result?.scoring?.original_score ?? this.score; },
        get insightAdjustment() { return this.result?.scoring?.insight_adjustment ?? 0; },
        get riskCategory() { return this.result?.scoring?.risk_category ?? 'N/A'; },

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

        get loan() { return this.result?.scoring?.loan_recommendation ?? {}; },
        get bankScores() { return this.result?.scoring?.bank_scores ?? []; },
        get bankSummary() { return this.result?.scoring?.bank_summary ?? 'Bank assessment summary not available.'; },
        get intelligence() { return this.result?.intelligence ?? {}; },
        get financial() { return this.result?.financial_data ?? {}; },
        get breakdown() { return this.result?.scoring?.risk_breakdown ?? {}; },
        get fiveCs() { return this.result?.scoring?.five_cs ?? []; },
        get riskNarrative() { return this.result?.scoring?.risk_narrative ?? 'Risk narrative not available.'; },
        get officerInsights() { return this.result?.scoring?.officer_insights ?? this.result?.company_info?.insights ?? ''; },

        getRiskExplanation() {
            const finalScore = this.score;
            const aiScore = this.originalScore;
            const adj = this.insightAdjustment;
            const insights = this.officerInsights;

            // Part 1: AI-generated score
            let html = `<strong>AI-Generated Score:</strong> The federated AI model analyzed the company's financial data, compliance records, legal history, and market signals to generate a base credit score of <strong>${aiScore}/1000</strong>.`;

            // Part 2: Officer insight adjustment
            if (adj !== 0) {
                const direction = adj > 0 ? 'increased' : 'decreased';
                const dirColor = adj > 0 ? '#10b981' : '#ef4444';
                const arrow = adj > 0 ? '▲' : '▼';
                html += `<br/><br/><strong>Officer Insight Adjustment:</strong> Based on the credit officer's primary insights, the score was <span style="color:${dirColor};font-weight:600">${arrow} ${direction} by ${Math.abs(adj)} points</span> — from ${aiScore} to <strong>${finalScore}/1000</strong>.`;
            } else {
                html += `<br/><br/><strong>Officer Insight Adjustment:</strong> The officer's assessment did not result in any score adjustment. The final score remains at <strong>${finalScore}/1000</strong>.`;
            }

            // Part 3: Officer insights text
            if (insights && insights.trim()) {
                html += `<br/><br/><strong>Officer's Assessment:</strong> <em>"${insights.trim()}"</em>`;
            }

            // Part 4: Risk interpretation
            html += `<br/><br/><strong>Risk Interpretation:</strong> `;
            if (finalScore >= 700) {
                html += `A final score of ${finalScore}/1000 indicates <span style="color:#10b981;font-weight:600">strong creditworthiness</span>. The company demonstrates solid financial health, regulatory compliance, and positive market signals. Lenders can extend credit with high confidence at competitive rates.`;
            } else if (finalScore >= 400) {
                html += `A final score of ${finalScore}/1000 reflects <span style="color:#f59e0b;font-weight:600">moderate creditworthiness</span>. The company has acceptable fundamentals but shows areas that need improvement. Lenders may proceed with standard risk provisioning and monitoring.`;
            } else {
                html += `A final score of ${finalScore}/1000 signals <span style="color:#ef4444;font-weight:600">significant credit risk</span>. Multiple indicators raise concerns. Detailed due diligence is heavily recommended.`;
            }

            return html;
        },

        getFinancialSummary() {
            // Prefer the LLM-generated executive summary if available
            if (this.result?.llm_executive_summary) {
                return this.result.llm_executive_summary;
            }

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

            if (parts.length === 0) return 'Financial metrics were not fully extracted.';
            return parts.join('. ') + '.';
        },

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

        initChart() {
            const ctx = document.getElementById('riskChart');
            if (!ctx || typeof Chart === 'undefined') return;

            // Destroy existing chart if any
            let chartStatus = Chart.getChart("riskChart");
            if (chartStatus != undefined) {
                chartStatus.destroy();
            }

            const labels = Object.keys(this.breakdown);
            const data = Object.values(this.breakdown);

            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{
                        data,
                        backgroundColor: ['#6366f1', '#22d3ee', '#f59e0b', '#10b981'],
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
                                font: { family: "'Inter', sans-serif", size: 12 },
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
                        },
                    },
                },
            });
        },

        async downloadReport() {
            const id = this.result?.analysis_id || this.currentSessionId;
            if (!id) return;

            try {
                const response = await fetch(`/api/report/${id}`);
                if (!response.ok) throw new Error('Failed to download report');

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `FedCredit_CAM_Report_${id.substring(0, 8)}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
            } catch (err) {
                alert('Report download failed: ' + err.message);
            }
        },

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
