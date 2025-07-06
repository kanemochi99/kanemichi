document.addEventListener('DOMContentLoaded', () => {
    const treeContainer = document.getElementById('treeContainer');
    const addNodeButton = document.getElementById('addNode');
    const removeNodeButton = document.getElementById('removeNode');
    const exportTreeButton = document.getElementById('exportTree');

    let nodeIdCounter = 0;
    let cy; // Cytoscape instance

    // --- Cytoscape.jsの初期化 ---
    function initializeCytoscape(elements = []) {
        cy = cytoscape({
            container: treeContainer,
            elements: elements,
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': '#e7f3ff',
                        'border-color': '#007bff',
                        'border-width': 1,
                        'label': 'data(text)', // ノードのテキストをラベルとして表示
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'width': 'label', // ラベルの幅に合わせる
                        'height': 'label',
                        'padding': '10px',
                        'shape': 'round-rectangle', // 角丸四角形
                        // 画像表示のためのスタイル
                        'background-image': 'data(imageUrl)', // imageUrlプロパティから画像URLを取得
                        'background-fit': 'contain', // 画像をノード内に収める
                        'background-clip': 'node', // 画像のクリッピングをノードに合わせる
                        'background-opacity': 0.5, // 画像がテキストと重なる場合、少し透明にする (任意)
                        'text-wrap': 'wrap', // テキストを折り返す
                        'text-max-width': '100px' // テキストの最大幅 (ノードサイズに影響)
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#007bff',
                        'target-arrow-color': '#007bff',
                        'target-arrow-shape': 'triangle', // 矢印の形状
                        'curve-style': 'bezier' // または 'straight', 'haystack' など
                    }
                },
                {
                    selector: 'node:selected',
                    style: {
                        'border-color': 'red',
                        'border-width': 2
                    }
                }
            ],
            layout: {
                name: 'dagre', //dagreレイアウトを使用
                rankDir: 'TB', // Top to Bottom
                spacingFactor: 1.2
            }
        });

        // --- Cytoscapeイベントハンドラ ---
        cy.on('tap', 'node', (event) => {
            const node = event.target;
            const externalLink = node.data('externalLink');

            if (externalLink) {
                // リンクがあれば新しいタブで開く
                // ユーザーが意図しないポップアップを防ぐため、直接のユーザーアクション（タップ）で開くのが一般的
                // Cytoscapeの選択イベントも発火するが、リンクを開くことを優先
                // 選択状態のハンドリングはCytoscapeのデフォルトに任せる
                window.open(externalLink, '_blank');
                console.log('外部リンクを開きました:', externalLink);
                // リンクを開いた後、ノードの選択状態を維持または解除するかは設計次第
                // ここでは特に何もしない（Cytoscapeのデフォルトの選択挙動）
            }
            // console.log('ノード選択 (Cytoscape):', node.id());
        });

        cy.on('tap', (event) => {
            if (event.target === cy) {
                // console.log('背景クリック (Cytoscape)');
                // 背景クリックで選択解除はCytoscapeのデフォルト挙動
            }
        });

        cy.on('dbltap', 'node', (event) => {
            const node = event.target;
            const currentText = node.data('text') || '';
            const currentImageUrl = node.data('imageUrl') || '';
            const currentExternalLink = node.data('externalLink') || '';

            const newText = prompt('ノードのテキストを入力してください:', currentText);
            if (newText !== null) { // キャンセルでなければ
                node.data('text', newText.trim());

                const newImageUrl = prompt('画像URLを入力してください (任意):', currentImageUrl);
                if (newImageUrl !== null) { // キャンセルでなければ
                    node.data('imageUrl', newImageUrl.trim() || null); // 空文字ならnull
                }

                const newExternalLink = prompt('外部リンクURLを入力してください (任意):', currentExternalLink);
                if (newExternalLink !== null) { // キャンセルでなければ
                    node.data('externalLink', newExternalLink.trim() || null); // 空文字ならnull
                }

                // スタイルやレイアウトの更新が必要な場合がある
                // Cytoscapeはdataの変更を検知してスタイルを再適用するはず
                // runLayout(); // 必要に応じてレイアウトも更新
            }
        });
    }

    // --- レイアウト実行関数 ---
    function runLayout() {
        cy.layout({
            name: 'dagre',
            rankDir: 'TB',
            spacingFactor: 1.2,
            animate: true,
            animationDuration: 300
        }).run();
    }

    // --- ノードとエッジのデータをCytoscape形式に変換 ---
    // (この関数は直接は使われなくなり、追加・削除時に直接cyオブジェクトを操作する)
    // function convertToCytoscapeElements(nodesData) {
    //     const elements = [];
    //     nodesData.forEach(node => {
    //         elements.push({ data: { id: node.id, text: node.text } });
    //         if (node.parentId) {
    //             const edgeId = `edge-${node.parentId}-to-${node.id}`;
    //             elements.push({ data: { id: edgeId, source: node.parentId, target: node.id } });
    //         }
    //     });
    //     return elements;
    // }

    // --- ノード追加機能 ---
    addNodeButton.addEventListener('click', () => {
        nodeIdCounter++;
        const newNodeId = `node-${nodeIdCounter}`;
        const selectedNodes = cy.nodes(':selected');
        let parentId = null;

        if (selectedNodes.length > 0) {
            parentId = selectedNodes[0].id(); // 最初に選択されたノードを親とする
        }

        const newNodeData = {
            group: 'nodes',
            data: {
                id: newNodeId,
                text: `ノード ${nodeIdCounter}`
            }
        };
        cy.add(newNodeData);
        console.log('ノード追加 (Cytoscape):', newNodeId);

        if (parentId) {
            const newEdgeData = {
                group: 'edges',
                data: {
                    id: `edge-${parentId}-to-${newNodeId}`,
                    source: parentId,
                    target: newNodeId
                }
            };
            cy.add(newEdgeData);
            console.log('エッジ追加 (Cytoscape):', newEdgeData.data.id);
        }
        runLayout();
    });

    // --- ノード削除機能 ---
    removeNodeButton.addEventListener('click', () => {
        const selectedNodes = cy.nodes(':selected');
        if (selectedNodes.length === 0) {
            alert('削除するノードを選択してください。');
            return;
        }
        // Cytoscapeでは、ノードを削除すると接続されているエッジも自動的に削除される
        selectedNodes.remove();
        console.log('ノード削除 (Cytoscape):', selectedNodes.map(n => n.id()));
        runLayout(); // レイアウトを再実行
    });

    // --- エクスポート機能 ---
    exportTreeButton.addEventListener('click', () => {
        if (!cy || cy.elements().length === 0) {
            alert('エクスポートするツリーがありません。');
            return;
        }

        // PNGとしてエクスポート
        const png64 = cy.png({
            output: 'base64uri', // base64文字列で取得
            bg: 'white',         // 背景色
            full: true,          // 全体を描画
            scale: 2             // 解像度を2倍に (任意)
        });

        // ダウンロードリンクを作成してクリック
        const link = document.createElement('a');
        link.download = 'logic-tree.png';
        link.href = png64;
        document.body.appendChild(link); // Firefoxで必要
        link.click();
        document.body.removeChild(link);

        console.log('ツリーをPNGとしてエクスポートしました。');
    });


    // --- 初期化 ---
    initializeCytoscape();
    // 初期サンプルノード (デバッグ用)
    // cy.add([
    //     { data: { id: 'n1', text: 'ルート' } },
    //     { data: { id: 'n2', text: '子1' } },
    //     { data: { id: 'n3', text: '子2' } },
    //     { data: { id: 'n4', text: '孫1-1' } },
    //     { data: { source: 'n1', target: 'n2' } },
    //     { data: { source: 'n1', target: 'n3' } },
    //     { data: { source: 'n2', target: 'n4' } }
    // ]);
    // runLayout();

});
