#!/usr/bin/env python
import keras, tensorflow as tf, numpy as np, gym, sys, copy, argparse
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.optimizers import Adam
import collections
import time

class QNetwork():

	# This class essentially defines the network architecture. 
	# The network should take in state of the world as an input, 
	# and output Q values of the actions available to the agent as the output. 

	def __init__(self, env):
		# Define your network architecture here. It is also a good idea to define any training operations 
		# and optimizers here, initialize your variables, or alternately compile your model here.  
		self.learning_rate = 0.0001
		
		self.model = Sequential()
		self.model.add(Dense(env.action_space.n, input_dim = env.observation_space.shape[0], kernel_initializer='he_uniform'))
		self.model.add(Activation('linear'))
		self.model.compile(optimizer = Adam(lr=self.learning_rate), loss='mse')

	def save_model_weights(self, suffix):
		# Helper function to save your model / weights. 
		self.model.save_weights(suffix)
		
	def load_model(self, model_file):
		# Helper function to load an existing model.
		self.model = keras.models.load_model(model_file)

	def load_model_weights(self,weight_file):
		# Helper funciton to load model weights. 
		# self.model.load_weights(weight_file)
		self.model.set_weights(weight_file)
		

class Replay_Memory():

	def __init__(self, memory_size=50000, burn_in=10000):

		# The memory essentially stores transitions recorder from the agent
		# taking actions in the environment.

		# Burn in episodes define the number of episodes that are written into the memory from the 
		# randomly initialized agent. Memory size is the maximum size after which old elements in the memory are replaced. 
		# A simple (if not the most efficient) was to implement the memory is as a list of transitions. 
		pass

	def sample_batch(self, batch_size=32):
		# This function returns a batch of randomly sampled transitions - i.e. state, action, reward, next state, terminal flag tuples. 
		# You will feed this to your model to train.
		pass

	def append(self, transition):
		# Appends transition to the memory. 	
		pass

class DQN_Agent():

	# In this class, we will implement functions to do the following. 
	# (1) Create an instance of the Q Network class.
	# (2) Create a function that constructs a policy from the Q values predicted by the Q Network. 
	#		(a) Epsilon Greedy Policy.
	# 		(b) Greedy Policy. 
	# (3) Create a function to train the Q Network, by interacting with the environment.
	# (4) Create a function to test the Q Network's performance on the environment.
	# (5) Create a function for Experience Replay.
	
	def __init__(self, env, replay=False, render=False):

		# Create an instance of the network itself, as well as the memory. 
		# Here is also a good place to set environmental parameters,
		# as well as training parameters - number of episodes / iterations, etc. 
		self.net = QNetwork(env)
		self.prediction_net = QNetwork(env)

		self.env = env
		self.replay = replay
		self.render = render
		self.feature_size = env.observation_space.shape[0]
		self.action_size = env.action_space.n
		
		self.discount_factor = 1
		self.train_iters = 1000000
		self.epsilon = 0.5
		self.num_episodes = 3000
		# self.epsilon_decay = float(0.65/self.train_iters)
		self.epsilon_decay = 0.99
		self.update_epsilon_iters = 250
		self.update_prediction_net_iters = 1
		self.avg_rew_buf_size_epi = 5
		self.save_weights_iters = 1000
		self.print_epi = 1

	def epsilon_greedy_policy(self, q_values):
		# Creating epsilon greedy probabilities to sample from.             
		if(np.random.random_sample()<self.epsilon):
			return np.random.randint(self.action_size)
		else:
			return np.argmax(q_values[0])

	def greedy_policy(self, q_values):
		# Creating greedy policy for test time. 
		pass

	def train(self):
		# In this function, we will train our network. 
		# If training without experience replay_memory, then you will interact with the environment 
		# in this function, while also updating your network parameters.
		curr_episode = 1
		iters = 1
		max_reward = 0
		reward_buf = collections.deque()
		
		if(self.replay==False):
			# while(True):
			for e in range(self.num_episodes):
				# time.sleep(1)
				curr_reward = 0
				curr_state = self.env.reset()
				curr_state = curr_state.reshape([1,self.feature_size])
				curr_action = self.epsilon_greedy_policy(self.prediction_net.model.predict(curr_state))

				# while(iters<self.train_iters):
				while(True):
					self.env.render()
					nextstate, reward, is_terminal, debug_info = self.env.step(curr_action)
					curr_reward += reward
					
					truth = np.zeros(shape=[1,self.action_size])
					
					##### changed #####
					# if(is_terminal == True):
					if(nextstate[0]>=0.5):
						# print(is_terminal, reward, bool(nextstate[0]>=0.6))
						q_target = reward
						truth = self.net.model.predict(curr_state)
						truth[0][curr_action] = q_target
						self.net.model.fit(curr_state,truth,epochs=1,verbose=0)	
						break
					
					nextstate = nextstate.reshape([1,self.feature_size])
					q_nextstate = self.prediction_net.model.predict(nextstate)
					nextaction = self.epsilon_greedy_policy(q_nextstate)
					q_target = reward + self.discount_factor*q_nextstate[0][nextaction]

					truth = self.net.model.predict(curr_state)
					truth[0][curr_action] = q_target

					self.net.model.fit(curr_state,truth,epochs=1,verbose=0)	
					
					curr_state = nextstate
					curr_action = nextaction

					iters += 1

					if(iters%self.update_epsilon_iters==0):
						self.epsilon *= self.epsilon_decay
						self.epsilon = max(self.epsilon, 0.05)
					if(iters%self.update_prediction_net_iters == 0):
						self.prediction_net.load_model_weights(self.net.model.get_weights())
					# if(iters%self.save_weights_iters==0):
						# self.net.save_model_weights(weights)
					print(self.epsilon, iters)
				
				###end of episode##	
				
				###rewards
				
				max_reward = max(max_reward, curr_reward)

				if(len(reward_buf)>self.avg_rew_buf_size_epi):
					reward_buf.popleft()
				reward_buf.append(curr_reward)
				avg_reward = sum(reward_buf)/len(reward_buf)
				
				if(curr_episode%self.print_epi==0):
					print(curr_episode, iters, curr_reward, avg_reward, self.epsilon)	
				curr_episode += 1

		# If you are using a replay memory, you should interact with environment here, and store these 
		# transitions to memory, while also updating your model.
		elif(self.replay):
			pass

	def test(self, model_file=None):
		# Evaluate the performance of your agent over 100 episodes, by calculating cummulative rewards for the 100 episodes.
		# Here you need to interact with the environment, irrespective of whether you are using a memory. 
		pass

	def burn_in_memory():
		# Initialize your replay memory with a burn_in number of episodes / transitions. 

		pass

def parse_arguments():
	parser = argparse.ArgumentParser(description='Deep Q Network Argument Parser')
	parser.add_argument('--env',dest='env',type=str)
	parser.add_argument('--render',dest='render',type=int,default=0)
	parser.add_argument('--train',dest='train',type=int,default=1)
	parser.add_argument('--model',dest='model_file',type=str)
	parser.add_argument('--replay',dest='replay',type=str,default=False)
	return parser.parse_args()


def main(args):


	args = parse_arguments()
	environment_name = args.env
	env = gym.make(environment_name)

	# Setting the session to allow growth, so it doesn't allocate all GPU memory. 
	gpu_ops = tf.GPUOptions(allow_growth=True)
	config = tf.ConfigProto(gpu_options=gpu_ops)
	sess = tf.Session(config=config)

	# Setting this as the default tensorflow session. 
	keras.backend.tensorflow_backend.set_session(sess)

	# You want to create an instance of the DQN_Agent class here, and then train / test it. 
	agent = DQN_Agent(env)
	agent.train()


if __name__ == '__main__':
	main(sys.argv)
