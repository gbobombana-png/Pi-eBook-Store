using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Blockside.Editor
{
    /// <summary>
    /// Script de build automatisé — appel via ligne de commande ou menu Unity.
    ///
    /// Build CLI (depuis la racine du projet Unity) :
    ///   Unity -batchmode -quit -projectPath . -executeMethod Blockside.Editor.BuildAutomation.BuildAndroid
    ///
    /// Build Debug :
    ///   Unity -batchmode -quit -projectPath . -executeMethod Blockside.Editor.BuildAutomation.BuildAndroidDebug
    /// </summary>
    public static class BuildAutomation
    {
        private const string AppId        = "com.blockside.pinetwork";
        private const string AppName      = "BLOCKSIDE";
        private const string BuildVersion = "1.0.0";
        private const int    BuildNumber  = 1;

        // ── Scènes dans l'ordre de build ─────────────────────────────
        private static readonly string[] Scenes =
        {
            "Assets/Scenes/BootstrapScene.unity",
            "Assets/Scenes/SplashScene.unity",
            "Assets/Scenes/CharacterSelectScene.unity",
            "Assets/Scenes/HubScene.unity",
            "Assets/Scenes/CityMapScene.unity",
            "Assets/Scenes/DistrictScene.unity",
        };

        // ── Builds menu Unity ─────────────────────────────────────────
        [MenuItem("BLOCKSIDE/Build Android Release")]
        public static void BuildAndroid() => Build(BuildOptions.None, "release");

        [MenuItem("BLOCKSIDE/Build Android Debug")]
        public static void BuildAndroidDebug() => Build(BuildOptions.Development | BuildOptions.AllowDebugging, "debug");

        [MenuItem("BLOCKSIDE/Build Android APK (release)")]
        public static void BuildAndroidApk()
        {
            EditorUserBuildSettings.buildAppBundle = false;
            Build(BuildOptions.None, "release-apk");
        }

        // ── Logique commune ───────────────────────────────────────────
        static void Build(BuildOptions opts, string tag)
        {
            ConfigurePlayer();

            string outputDir = Path.Combine(Directory.GetCurrentDirectory(), "Builds", "Android");
            Directory.CreateDirectory(outputDir);

            bool isApk = !EditorUserBuildSettings.buildAppBundle;
            string ext = isApk ? ".apk" : ".aab";
            string filename = $"{AppName}_{BuildVersion}_b{BuildNumber}_{tag}{ext}";
            string outputPath = Path.Combine(outputDir, filename);

            var buildParams = new BuildPlayerOptions
            {
                scenes          = FilterExistingScenes(Scenes),
                locationPathName = outputPath,
                target          = BuildTarget.Android,
                options         = opts,
            };

            Debug.Log($"[Build] Démarrage build {tag} → {outputPath}");
            var report = BuildPipeline.BuildPlayer(buildParams);
            LogReport(report, outputPath);
        }

        static void ConfigurePlayer()
        {
            // Identité
            PlayerSettings.applicationIdentifier              = AppId;
            PlayerSettings.productName                        = AppName;
            PlayerSettings.bundleVersion                      = BuildVersion;
            PlayerSettings.Android.bundleVersionCode          = BuildNumber;

            // Affichage
            PlayerSettings.defaultInterfaceOrientation        = UIOrientation.Portrait;
            PlayerSettings.allowedAutorotateToPortrait        = true;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
            PlayerSettings.allowedAutorotateToLandscapeLeft   = false;
            PlayerSettings.allowedAutorotateToLandscapeRight  = false;
            PlayerSettings.statusBarHidden                    = true;

            // Performances Android
            PlayerSettings.Android.minSdkVersion              = AndroidSdkVersions.AndroidApiLevel24;
            PlayerSettings.Android.targetSdkVersion           = AndroidSdkVersions.AndroidApiLevel34;
            PlayerSettings.Android.targetArchitectures        = AndroidArchitecture.ARM64 | AndroidArchitecture.ARMv7;
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.forceInternetPermission    = true;
            PlayerSettings.Android.forceSDCardPermission      = false;

            // Qualité
            QualitySettings.SetQualityLevel(2, true); // Medium par défaut

            // API compatibility
            PlayerSettings.SetApiCompatibilityLevel(BuildTargetGroup.Android, ApiCompatibilityLevel.NET_Standard);

            Debug.Log("[Build] PlayerSettings configurés.");
        }

        static string[] FilterExistingScenes(string[] scenes)
        {
            var existing = scenes.Where(s => File.Exists(Path.Combine(Directory.GetCurrentDirectory(), s))).ToArray();
            if (existing.Length == 0)
            {
                // Fallback : toutes les scènes enregistrées dans EditorBuildSettings
                existing = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
                Debug.LogWarning($"[Build] Aucune scène trouvée dans la liste prédéfinie — utilisation des scènes EditorBuildSettings ({existing.Length}).");
            }
            return existing;
        }

        static void LogReport(BuildReport report, string outputPath)
        {
            var summary = report.summary;
            if (summary.result == BuildResult.Succeeded)
            {
                double sizeMb = summary.totalSize / 1048576.0;
                Debug.Log($"[Build] ✅ SUCCÈS — {outputPath} ({sizeMb:F1} Mo) en {summary.totalTime.TotalSeconds:F0}s");
            }
            else
            {
                Debug.LogError($"[Build] ❌ ÉCHEC ({summary.result}) — {summary.totalErrors} erreur(s)");
                foreach (var step in report.steps)
                    foreach (var msg in step.messages)
                        if (msg.type == LogType.Error)
                            Debug.LogError($"  [{step.name}] {msg.content}");

                if (Application.isBatchMode) EditorApplication.Exit(1);
            }
        }
    }
}
