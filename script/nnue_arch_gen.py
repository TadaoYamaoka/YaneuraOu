# NNUE architecture header generator
#
#  NNUE評価関数のarchitecture headerを動的に生成するPythonで書かれたスクリプト。
# 

import argparse
import os
import textwrap

print("NNUE architecture header generator by yaneurao V1.00 , 2024/06/25")

parser = argparse.ArgumentParser(description="NNUEのarchitecture headerを生成する。")
parser.add_argument('arch', type=str, nargs='?', default="halfkp_256x2-32-32", help="architectureを指定する。例) halfkp_1024x2-8-64")
parser.add_argument('out_dir', type=str, nargs='?', default="", help="出力先のフォルダを指定する。例) /source/eval/nnue/architectures/")

args = parser.parse_args()

arch    : str = args.arch
out_dir : str = args.out_dir

print(f"architecture name : {arch}")

# 出力ファイル名
filename = arch + ".h"

# 出力file path
out_path = os.path.join(out_dir, filename)

print(f"output file path  : {out_path}")

if os.path.exists(out_path):
    print("Warning : file always exists. stop.")
    exit()

# 大文字化して、'-'を'_'に置換したアーキテクチャ名
c_arch = arch.upper().replace('-','_')

arches = arch.split('_')
if len(arches) !=2 :
    # アーキテクチャ名は、アンダースコアは1つだけ存在しないと駄目。
    print("Error! : architecture name must have exactly one underscore, like halfkp_256x2-32-32 or kp_256x2-32-32 halfkpvm_256x2-32-32")
    exit()

# ============================================================
#                        includes
# ============================================================

header = f"""
    // Definition of input features and network structure used in NNUE evaluation function
    // NNUE評価関数で用いる入力特徴量とネットワーク構造の定義
    #ifndef NNUE_{c_arch}_H_INCLUDED
    #define NNUE_{c_arch}_H_INCLUDED
    """

# ============================================================
#                     input features
# ============================================================

# アーキテクチャ名のアンダースコアでsplitした1つ目は入力特徴量。
# 現在サポートしている入力特徴量は、"halfkp" , "kp" , "halfkpvm" , "halfkpe9"。
input_feature = arches[0]

print(f"input feature     : {input_feature}")

header += f"""
    #include "../features/feature_set.h"
    """

if input_feature == "halfkp":

    header += f"""
    #include "../features/half_kp.h"
    """

    raw_features = f"""
        using RawFeatures = Features::FeatureSet<
            Features::HalfKP<Features::Side::kFriend>>;
    """

elif input_feature == "halfkpe9":

    header += f"""
    #include "../features/half_kpe9.h"
    """

    raw_features = f"""
        using RawFeatures = Features::FeatureSet<
            Features::HalfKPE9<Features::Side::kFriend>>;
    """

elif input_feature == "halfkpvm":

    header += f"""
    #include "../features/half_kp_vm.h"
    """

    raw_features = f"""
        using RawFeatures = Features::FeatureSet<
            Features::HalfKP_vm<Features::Side::kFriend>>;
    """

elif input_feature == "kp":

    header += f"""
    #include "../features/k.h"
    #include "../features/p.h"
    """
    
    raw_features = f"""
        using RawFeatures = Features::FeatureSet<Features::K, Features::P>;
    """

else:
    # 知らない入力特徴量だった。
    print(f"Error : input feature {input_feature} is not supported.")
    exit()

header += f"""
    #include "../layers/input_slice.h"
    #include "../layers/affine_transform.h"
    #include "../layers/clipped_relu.h"

    namespace Eval::NNUE {{

        // Input features used in evaluation function
        // 評価関数で用いる入力特徴量
    """

header += raw_features

# ============================================================
#                     hidden layers
# ============================================================

# レイヤ情報
# 例えば、"256x2-32-32" ならば ["256x2","32","32"]のように分解される。
layers = arches[1].split('-')

if len(layers) != 3 or len(layers[0].split('x')) != 2:
    print(f"Error : layers must be like 256x2-32-32 , layers = {arches[1]}.")
    exit()

first_layer = layers[0].split('x')

print(f"layers feature    : {layers}")

header += f"""
        // Number of input feature dimensions after conversion
        // 変換後の入力特徴量の次元数
        constexpr IndexType kTransformedFeatureDimensions = {first_layer[0]};

        namespace Layers {{

            // Define network structure
            // ネットワーク構造の定義
            using InputLayer = InputSlice<kTransformedFeatureDimensions * {first_layer[1]}>;
            using HiddenLayer1 = ClippedReLU<AffineTransform<InputLayer, {layers[1]}>>;
            using HiddenLayer2 = ClippedReLU<AffineTransform<HiddenLayer1, {layers[2]}>>;
            using OutputLayer = AffineTransform<HiddenLayer2, 1>;

        }}  // namespace Layers
    """

# ============================================================
#                     output layer
# ============================================================

header += f"""
        using Network = Layers::OutputLayer;

    }}  // namespace Eval::NNUE

    #endif // #ifndef NNUE_{c_arch}_H_INCLUDED
    """

with open(out_path, "w") as f:
    f.write(textwrap.dedent(header).lstrip())
    # lstrip()は先頭行の改行の除去。ここでやらないとdedentが誤作動する。

print("..done!")
