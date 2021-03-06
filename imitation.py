import sys
import argparse
import numpy as np
import keras
import random
import gym
from keras.utils import plot_model
from keras.optimizers import Adam

class Imitation():
    def __init__(self, model_config_path, expert_weights_path):
        # Load the expert model.
        with open(model_config_path, 'r') as f:
            self.expert = keras.models.model_from_json(f.read())
        self.expert.load_weights(expert_weights_path)
        plot_model(self.expert, to_file='imitation_expert_model.png', show_shapes = True)
        # self.expert.summary()

        # Initialize the cloned model (to be trained).
        with open(model_config_path, 'r') as f:
            self.model = keras.models.model_from_json(f.read())
        plot_model(self.model, to_file='imitation_model.png', show_shapes = True)           
        # self.model.summary()

        # TODO: Define any training operations and optimizers here, initialize
        #       your variables, or alternatively compile your model here.
        self.learning_rate = 0.0005
        self.model.compile(optimizer = Adam(lr=self.learning_rate), loss='categorical_crossentropy', metrics=['acc'])

    def run_expert(self, env, render=False):
        # Generates an episode by running the expert policy on the given env.
        return Imitation.generate_episode(self.expert, env, render)

    def run_model(self, env, render=False):
        # Generates an episode by running the cloned policy on the given env.
        return Imitation.generate_episode(self.model, env, render)

    @staticmethod
    def make_one_hot(env, action):
        one_hot_action_vector = np.zeros(env.action_space.n)
        one_hot_action_vector[action] = 1
        return one_hot_action_vector

    @staticmethod
    def generate_episode(model, env, render=False):
        # Generates an episode by running the given model on the given env.
        # Returns:
        # - a list of states, indexed by time step
        # - a list of actions, indexed by time step
        # - a list of rewards, indexed by time step
        # TODO: Implement this method.
        states = []
        actions = []
        rewards = []

        state = env.reset()
        action = np.argmax(model.predict(state.reshape([1,env.observation_space.shape[0]])))
        while(True):
            if(render==True):
                env.render()

            state = state.reshape([1,env.observation_space.shape[0]])
            states.append(state)                                            #storing reshaped state
            actions.append(Imitation.make_one_hot(env,action))              #storing one hot action target

            nextstate, reward, is_terminal, _ = env.step(action)
    
            rewards.append(reward)                                          #storing reward
            if(is_terminal == True):
                break                            
            state = nextstate.reshape([1,env.observation_space.shape[0]])
            action = np.argmax(model.predict(state))
        return states, actions, rewards
    
    def train(self, env, num_episodes=100, num_epochs=50, render=False):
        
        loss = 0
        acc = 0

        current_episode = 0
        while(current_episode<num_episodes):
            #Generate episode as current training batch
            states,actions,_ = self.run_expert(env,False)
            current_batch_size = len(states)
            # history = self.model.fit(np.vstack(states),np.asarray(actions),epochs=1,verbose=0,batch_size=current_batch_size)
            history = self.model.fit(np.vstack(states),np.asarray(actions),epochs=num_epochs,verbose=0)
            current_episode += 1
            acc = history.history['acc']
            print("Episode: {}, Accuracy: {} ".format(current_episode, history.history['acc'][-1]))

        self.model.save("behaviour_cloning/"+"episode_"+str(num_episodes))
        return acc[-1]

    def test(self, env, num_episodes=50, render=False):
        current_episode = 0
        rewards = []
        while(current_episode<num_episodes):
            # if(render==True):
                # env.render()
            _,_,r = self.run_model(env,render=False)
            rewards.append(np.sum(r))
            current_episode +=1

        return np.std(np.hstack(rewards)),np.mean(np.hstack(rewards))

    def test_expert(self, env, num_episodes=100, render=False):
        current_episode = 0
        rewards = []
        while(current_episode<num_episodes):
            # if(render==True):
                # env.render()
            _,_,r = self.run_expert(env,render=False)
            rewards.append(np.sum(r))
            current_episode +=1

        return np.std(np.hstack(rewards)),np.mean(np.hstack(rewards))

def parse_arguments():
    # Command-line flags are defined here.
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-config-path', dest='model_config_path',
                        type=str, default='LunarLander-v2-config.json',
                        help="Path to the model config file.")
    parser.add_argument('--expert-weights-path', dest='expert_weights_path',
                        type=str, default='LunarLander-v2-weights.h5',
                        help="Path to the expert weights file.")

    # https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    parser_group = parser.add_mutually_exclusive_group(required=False)
    parser_group.add_argument('--render', dest='render',
                              action='store_true',
                              help="Whether to render the environment.")
    parser_group.add_argument('--no-render', dest='render',
                              action='store_false',
                              help="Whether to render the environment.")
    parser.set_defaults(render=False)

    return parser.parse_args()


def main(args):
    # Parse command-line arguments.
    args = parse_arguments()
    model_config_path = args.model_config_path
    expert_weights_path = args.expert_weights_path
    render = args.render
    
    # Create the environment.
    env = gym.make('LunarLander-v2')
    
    # TODO: Train cloned models using imitation learning, and record their
    #       performance.
    imitating_agent = Imitation('LunarLander-v2-config.json','LunarLander-v2-weights.h5')
    episodes = 10
    epochs = 50
    acc = imitating_agent.train(env,episodes,epochs,render=args.render)

    # Test cloned policy
    std,mean = imitating_agent.test(env,render=args.render)
    # std_expert, std_mean = imitating_agent.test_expert(env)
    file_test = open('behaviour_cloning/accuracy.txt', 'a+')
    file_test.write("\n"+str(episodes)+" "+str(acc)+" "+"std: "+str(std)+" mean: "+str(mean))


if __name__ == '__main__':
  main(sys.argv)
 