import numpy as np 
import csv
from collections import defaultdict
import os
import random

states = {'H': 0,
					'G': 1,
					'I': 2,
					'B': 3,
					'E': 4,
					'T': 5,
					'S': 6,
					'-': 7,
					'X': 8,
					'Y': 8}

seq_max_len = 930

def load_protvec(filename):
	protvec = []
	key_aa = {}
	count = 0
	with open(filename, "rb") as csvfile:
		protvec_reader = csv.reader(csvfile, delimiter='\t')
		for k, row in enumerate(protvec_reader):
			if k == 0:
				continue
			protvec.append([float(x) for x in row[1:]])
			key_aa[row[0]] = count
			count = count + 1

	protvec.append([0.0] * 100)
	key_aa["zero"] = count
	return protvec, key_aa


def prepare_data(input_dir, ouput_dir):
	protvec, key_aa = load_protvec("protVec_100d_3grams.csv")
	protvec = np.asarray(protvec, dtype=np.float32)
	data = []
	label = []
	rel_label = []
	b_label = []
	sequence_length = []
	weight_mask = []
	weight_mask_ss = []
	
	for text_file in os.listdir(input_dir):
		fi = open(os.path.join(input_dir, text_file), "r")
		input_length = 0
		input_aa = ''
		for line in fi:
			if '>' in line:
				if input_length != 0:
					break
			else:
				input_aa = input_aa + line.rstrip()
				input_length = input_length + len(line.rstrip())

		input_vector = []
		check = True
		input_vector.append(key_aa["<unk>"])
		for i in range(1, input_length - 1):
			if input_aa[i-1:i+2] not in key_aa:
				check = False
				break
			input_vector.append(key_aa[input_aa[i-1:i+2]])

		if check == False:
			continue
		input_vector.append(key_aa["<unk>"])

		file_id = text_file.split('.')[0].lower()
		fo = open(os.path.join(ouput_dir, file_id + ".8.consensus.dssp"), "r")
		foo = np.memmap(os.path.join(ouput_dir, file_id + ".rel_asa.memmap"), dtype=np.float32, mode='r', shape=input_length)
		try:
			fooo = np.memmap(os.path.join(ouput_dir, file_id + ".bdb.memmap"), dtype=np.float32, mode='r', shape=input_length)
		except IOError:
			continue
		output_length = 0
		output_state = ''
		for line in fo:
			if '>' in line:
				if output_length != 0:
					break
			else:
				output_state = output_state + line.rstrip()
				output_length = output_length + len(line.rstrip())
		label_tmp = [states[x] for x in output_state]

		foo_tmp = []
		rel_label_tmp = []
		for rel in foo:
			if rel <= 0.09:
				foo_tmp.append(0)
			elif rel >= 0.36:
				foo_tmp.append(2)
			else:
				foo_tmp.append(1)
		
		fooo_tmp = []
		b_label_tmp = []
		for rel in fooo:
			if rel <= -1:
				fooo_tmp.append(0)
			elif rel >= 1:
				fooo_tmp.append(2)
			else:
				fooo_tmp.append(1)

		input_vector_tmp = []
		for i in range(len(label_tmp)):
			if label_tmp[i] == 8:
				input_length = input_length - 1
				continue
			else:
				input_vector_tmp.append(input_vector[i])
				rel_label_tmp.append(foo_tmp[i])
				b_label_tmp.append(fooo_tmp[i])

		label_tmp = [x for x in label_tmp if x != 8]

		
		for i in range(input_length, seq_max_len):
			input_vector_tmp.append(key_aa["zero"])
			label_tmp.append(random.choice([1, 2, 3]))
			rel_label_tmp.append(1)
			b_label_tmp.append(random.choice([0, 2]))
			#b_label_tmp.append(0)

		if len(input_vector_tmp) != 930:
			continue

		weight_mask_ss_tmp = []
		for l in label_tmp:
			if l == 0:
				weight_mask_ss_tmp.append(0.1)
			if l == 1:
				weight_mask_ss_tmp.append(0.7)
			if l == 2:
				weight_mask_ss_tmp.append(2.6)
			if l == 3:
				weight_mask_ss_tmp.append(3.9)
			if l == 4:
				weight_mask_ss_tmp.append(0.11)
			if l == 5:
				weight_mask_ss_tmp.append(0.25)
			if l == 6:
				weight_mask_ss_tmp.append(0.45)
			if l == 7:
				weight_mask_ss_tmp.append(0.2)


		weight_mask_tmp = []
		for l in b_label_tmp:
			if l == 0:
				weight_mask_tmp.append(0.95)
			if l == 1:
				weight_mask_tmp.append(0.2)
			if l == 2:
				weight_mask_tmp.append(0.7)

		weight_mask_ss.append(weight_mask_ss_tmp)
		weight_mask.append(weight_mask_tmp)
		label.append(label_tmp)
		data.append(input_vector_tmp)
		sequence_length.append(input_length)
		rel_label.append(rel_label_tmp)
		b_label.append(b_label_tmp)

		fi.close()
		fo.close()
	mask = []
	for length in sequence_length:
	  mask.append([1] * length + [0] * (930 - length))

	return data, label, mask, sequence_length, protvec, weight_mask, weight_mask_ss, rel_label, b_label
