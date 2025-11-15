library(jsonlite)
library(dplyr)
library(tidyr)
library(stringr)
library(readr)
library(purrr)

json_files <- list.files("~/Desktop/replication-pilotB", pattern = ".*_pilotB\\.json$", full.names = TRUE)

raw_data <- map_dfr(json_files, function(file) {
  data <- fromJSON(file, flatten = TRUE)
  return(data)
})

# extract experimental trials
exp_trials <- raw_data %>%
  filter(trial_type == "image-button-response", 
         task == "main_trial") %>%
  select(participant_id, trial_number, rt, response, 
         condition, category, memorability, target_image,
         drawing_filename, selected_image, selected_type,
         correct_position, correct, is_attention_check)

# extract attention checks
attention_checks <- raw_data %>%
  filter(trial_type == "image-button-response", 
         task == "attention_check") %>%
  select(participant_id, trial_number, response, correct)

# extract technical survey
tech_survey <- raw_data %>%
  filter(trial_type == "survey-multi-choice") %>%
  select(participant_id, response) %>%
  mutate(tech_difficulties = map_chr(response, ~ .x$technical_difficulties %||% "Unknown"))

# participant exclusions
attention_summary <- attention_checks %>%
  group_by(participant_id) %>%
  summarise(n_attention_failed = sum(!correct, na.rm = TRUE), .groups = "drop")

trial_summary <- exp_trials %>%
  filter(!is_attention_check) %>%
  group_by(participant_id) %>%
  summarise(
    n_trials = n(),
    median_rt = median(rt, na.rm = TRUE),
    overall_accuracy_delayed = mean(correct[condition == "delayed_recall"], na.rm = TRUE),
    .groups = "drop"
  )

participant_exclusions <- trial_summary %>%
  left_join(attention_summary, by = "participant_id") %>%
  left_join(select(tech_survey, participant_id, tech_difficulties), by = "participant_id") %>%
  mutate(
    exclude_attention = n_attention_failed >= 2,
    exclude_incomplete = n_trials < 60,
    exclude_tech = !is.na(tech_difficulties) & tech_difficulties != "No",  # if NA, then we can ignore it for now
    exclude_compliance = median_rt < 1000 | overall_accuracy_delayed < 0.333,
    exclude_any = exclude_attention | exclude_incomplete | exclude_tech | exclude_compliance
  )

retained_participants <- participant_exclusions %>%
  filter(!exclude_any) %>%
  pull(participant_id)

# calculate rt threshold for exclusions
# method 1: mean - 2.5*sd
all_exp_trials <- raw_data %>%
  filter(trial_type == "image-button-response", 
         task == "main_trial",
         !is_attention_check)

rt_mean <- mean(all_exp_trials$rt, na.rm = TRUE)
rt_sd <- sd(all_exp_trials$rt, na.rm = TRUE)
rt_threshold_sd <- rt_mean - 2.5 * rt_sd

cat("RT statistics for threshold calculation:\n")
cat("mean:", round(rt_mean), "ms\n")
cat("sd:", round(rt_sd), "ms\n") 
cat("threshold (mean - 2.5*sd):", round(rt_threshold_sd), "ms\n")

# choose threshold method!!!!!!
# option1: sd-based threshold
rt_threshold <- rt_threshold_sd

# option2: fixed threshold
# rt_threshold <- 500

cat("using rt threshold:", rt_threshold, "ms\n")

# trial exclusions  
exp_trials_filtered <- exp_trials %>%
  filter(participant_id %in% retained_participants,
         !is_attention_check) %>%
  mutate(exclude_rt = rt < rt_threshold) 

# check >20% rt exclusions per participant
rt_exclusion_check <- exp_trials_filtered %>%
  group_by(participant_id) %>%
  summarise(prop_excluded = mean(exclude_rt), .groups = "drop") %>%
  filter(prop_excluded > 0.20) %>%
  pull(participant_id)

final_participants <- setdiff(retained_participants, rt_exclusion_check)

# final clean dataset
clean_trials <- exp_trials_filtered %>%
  filter(participant_id %in% final_participants,
         !exclude_rt) %>%
  select(-exclude_rt)

# parse drawing metadata
clean_trials <- clean_trials %>%
  mutate(
    drawing_file = str_extract(drawing_filename, "[^/]+$"),
    drawing_id = case_when(
      condition == "delayed_recall" ~ paste0("delayed_", 
        str_extract(drawing_file, "^\\d+"), "_",
        str_extract(drawing_file, "(?<=_)\\d+(?=_)"), "_",
        memorability, "_", category),
      condition == "category" ~ paste0("category_", 
        str_extract(drawing_file, "^c\\d+"), "_",
        str_extract(drawing_file, "(?<=c\\d_)\\d+"), "_", 
        category),
      TRUE ~ NA_character_
    )
  )

# add debugging after each exclusion step
cat("initial participants:", length(unique(exp_trials$participant_id)), "\n")
cat("after attention check exclusions:", length(retained_participants), "\n")
cat("after rt exclusion check:", length(final_participants), "\n")

# check exclusion details
print("exclusion summary:")
print(participant_exclusions)
print("detailed exclusions:")
print(select(participant_exclusions, participant_id, exclude_attention, exclude_incomplete, exclude_tech, exclude_compliance, exclude_any))

# also check if final_participants is empty
if(length(final_participants) == 0) {
  cat("all participants excluded - skipping anonymization\n")
  clean_trials <- data.frame()  # empty dataset
} else {
  # continue with normal processing
}

# anonymize
if(length(final_participants) == 0) {
  cat("all participants excluded - creating empty dataset\n")
  clean_trials <- data.frame()
  write_csv(clean_trials, "../output/clean_trial_data.csv")
} else {
  participant_mapping <- data.frame(
    original_id = final_participants,
    anonymous_id = paste0("P", sprintf("%02d", seq_along(final_participants)))
  )
  
  clean_trials <- clean_trials %>%
    left_join(participant_mapping, by = c("participant_id" = "original_id")) %>%
    select(-participant_id) %>%
    rename(participant_id = anonymous_id)
  
  write_csv(clean_trials, "../output/clean_trial_data.csv")
}


write_csv(participant_exclusions, "../output/participant_exclusions.csv")