import torch
import matplotlib.pyplot as plt
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import seaborn as sns
from vllm import LLM, SamplingParams
from dataclasses import field

BATCH_SIZE = 4
NEW_TOKENS = [5, 10, 50]
REPEATS = 5

model_id = "models" # "jmvcoelho/GPTNeoX-160m" #"~/cmu11967-HW10/11967-hw10-dev-main/models/GPTNeoX-160M-WikiText-512-flash-attention-2-seq-len-2048-gradient-checkpointing"  #TODO: path to your model. You can use your trained model from the previous assignment, or the pretrained model you downloaded.

def timed_generate_huggingface():
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        device_map={"":0}, 
        use_auth_token=True
    )

    total_time_dict = {}
    text = [
            "hello"
        ] * BATCH_SIZE
    inputs = tokenizer(text, return_tensors="pt").to("cuda:0")

    for num_new_tokens in NEW_TOKENS:
        start_event = torch.cuda.Event(enable_timing=True)
        end_event = torch.cuda.Event(enable_timing=True)

        torch.cuda.empty_cache()
        torch.cuda.synchronize()

        start_event.record()
        for _ in range(REPEATS):
            # TODO: implement model.generate() here
            model.generate(**inputs, max_new_tokens=num_new_tokens)

        end_event.record()
        torch.cuda.synchronize()

        timing = (start_event.elapsed_time(end_event) * 1.0e-3) / REPEATS
        total_time_dict[f"{num_new_tokens}"] = timing
    
    return total_time_dict


def timed_generate_vllm():
    llm = LLM(model=model_id)
    total_time_dict={}
    text = [
            "hello"
    ] * BATCH_SIZE

    for num_new_tokens in NEW_TOKENS:
        # TODO: implement sampling_params = SamplingParams() with the correct arguments
        sampling_params = SamplingParams(
            max_tokens=num_new_tokens,
            temperature=0
        )

        start_event = torch.cuda.Event(enable_timing=True)
        end_event = torch.cuda.Event(enable_timing=True)

        torch.cuda.empty_cache()
        torch.cuda.synchronize()

        start_event.record()
        for _ in range(REPEATS):
            # TODO: implement llm.generate() here
            llm.generate(text, sampling_params=sampling_params)

        end_event.record()
        torch.cuda.synchronize()

        timing = (start_event.elapsed_time(end_event) * 1.0e-3) / REPEATS
        total_time_dict[f"{num_new_tokens}"] = timing
    
    return total_time_dict

def main():
    total_time_dict_huggingface = timed_generate_huggingface()
    total_time_dict_vllm = timed_generate_vllm()

    sns.set(style="darkgrid")

    # plot both lines
    sns.lineplot(data=total_time_dict_huggingface, color="blue", label="huggingface-generate")
    sns.lineplot(data=total_time_dict_vllm, color="red", label="vllm-generate")

    plt.ylabel("Average inference time (s)")
    plt.xlabel("Tokens Generated")
    plt.title("Comparing average inference time", fontsize = 8)

    plt.legend()

    # save plot
    plt.savefig("seaborn_comparison_plot.jpg", dpi=300)

if __name__ == '__main__':
    main()
